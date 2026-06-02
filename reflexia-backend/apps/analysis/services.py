import json

from django.conf import settings
from django.utils import timezone
from django.utils.html import strip_tags

from apps.analysis.models import EmotionalAnalysis
from apps.entries.models import JournalEntry
from apps.users.models import TherapistPatient


class AnalysisServiceError(Exception):
    pass


ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "emotions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "emotion": {"type": "string"},
                    "percentage": {"type": "number"},
                },
                "required": ["emotion", "percentage"],
                "additionalProperties": False,
            },
        },
        "primary_emotion": {"type": "string"},
        "risk_level": {"type": "string", "enum": ["none", "low", "moderate", "high"]},
        "summary": {"type": "string"},
        "recommendations": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "emotions",
        "primary_emotion",
        "risk_level",
        "summary",
        "recommendations",
    ],
    "additionalProperties": False,
}


SYSTEM_PROMPT = """
Ets un assistent de suport per a una plataforma de journaling terapèutic.
Analitza l'entrada del pacient amb prudència clínica i torna només JSON vàlid.
No diagnostiquis. El resultat és orientatiu i serà revisat per un terapeuta.
Identifica emocions amb percentatges que sumin aproximadament 100%.
Classifica el risc com none, low, moderate, high:
- none: No hi ha malestar evident ni senyals d'alarma.
- low: Malestar lleu o emocionalitat quotidiana sense senyals d'alarma.
- moderate: Malestar sostingut, desesperança o dificultats funcionals sense risc imminent.
- high: Autolesió, ideació suïcida no imminent, violència, abús o deteriorament intens.
Escriu resums i recomanacions en català, amb llenguatge clar i no alarmista, per guiar al pacient i ajudar-lo a reflexionar.
""".strip()


def analyze_journal_entry(*, entry):
    if entry.is_deleted:
        raise AnalysisServiceError("No es poden analitzar entrades eliminades.")

    payload = _request_openai_analysis(entry=entry)
    normalized_payload = _normalize_analysis_payload(payload)

    analysis, _ = EmotionalAnalysis.objects.update_or_create(
        entry=entry,
        defaults={
            "emotions": normalized_payload["emotions"],
            "primary_emotion": normalized_payload["primary_emotion"],
            "risk_level": normalized_payload["risk_level"],
            "summary": normalized_payload["summary"],
            "recommendations": normalized_payload["recommendations"],
            "analyzed_at": timezone.now(),
            "reviewed_by_therapist": False,
            "therapist_correction": "",
        },
    )

    entry.save(update_fields=["updated_at"])
    return analysis


def build_evolution_payload(*, patient):
    analyses = (
        EmotionalAnalysis.objects.filter(
            entry__patient=patient,
            entry__status__in=[JournalEntry.STATUS_ACTIVE, JournalEntry.STATUS_MODIFIED],
        )
        .select_related("entry")
        .order_by("entry__created_at")
    )
    data_points = []
    totals = {}
    occurrences = {}
    risk_counts = {}

    for analysis in analyses:
        emotion_map = {}
        for emotion_score in analysis.emotions:
            emotion = emotion_score.get("emotion", "").strip()
            percentage = float(emotion_score.get("percentage") or 0)
            if not emotion:
                continue
            emotion_map[emotion] = percentage
            totals[emotion] = totals.get(emotion, 0) + percentage
            occurrences[emotion] = occurrences.get(emotion, 0) + 1

        risk_counts[analysis.risk_level] = risk_counts.get(analysis.risk_level, 0) + 1
        data_points.append(
            {
                "entry_id": str(analysis.entry_id),
                "date": analysis.entry.created_at,
                "primary_emotion": analysis.primary_emotion,
                "risk_level": analysis.risk_level,
                "emotions": emotion_map,
            }
        )

    frequent_emotions = sorted(
        [
            {
                "emotion": emotion,
                "average_percentage": round(total / len(data_points), 2),
                "occurrences": occurrences[emotion],
            }
            for emotion, total in totals.items()
        ],
        key=lambda item: (item["occurrences"], item["average_percentage"]),
        reverse=True,
    )[:5]

    return {
        "analyzed_entries_count": len(data_points),
        "minimum_entries": 2,
        "has_enough_data": len(data_points) >= 2,
        "frequent_emotions": frequent_emotions,
        "risk_counts": risk_counts,
        "data_points": data_points,
        "message": (
            ""
            if len(data_points) >= 2
            else "Encara no hi ha prou entrades analitzades. Escriu i analitza més entrades per veure l'evolució."
        ),
    }


def _request_openai_analysis(*, entry):
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise AnalysisServiceError("La dependència openai no està instal·lada al backend.") from exc

    api_key = getattr(settings, "OPENAI_API_KEY", "")
    if not api_key:
        raise AnalysisServiceError("OPENAI_API_KEY no està configurada.")

    client = OpenAI(api_key=api_key)
    model_name = getattr(settings, "OPENAI_ANALYSIS_MODEL", "gpt-5.4-mini")
    context = build_entry_context(entry=entry)

    try:
        response = client.responses.create(
            model=model_name,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(context, ensure_ascii=False, default=str)},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "journal_entry_emotional_analysis",
                    "strict": True,
                    "schema": ANALYSIS_SCHEMA,
                }
            },
        )
    except Exception as exc:
        raise AnalysisServiceError("No s'ha pogut generar l'anàlisi amb OpenAI.") from exc

    try:
        parsed = json.loads(response.output_text)
    except (TypeError, ValueError) as exc:
        raise AnalysisServiceError("OpenAI ha retornat una resposta no vàlida.") from exc

    return parsed


def build_entry_context(*, entry):
    patient = entry.patient
    assigned_therapists = (
        TherapistPatient.objects.filter(patient=patient, is_active=True)
        .select_related("therapist")
        .order_by("created_at")
    )
    previous_analyses = (
        EmotionalAnalysis.objects.filter(entry__patient=patient, entry__created_at__lt=entry.created_at)
        .select_related("entry")
        .order_by("-entry__created_at")[:5]
    )

    return {
        "patient": {
            "id": str(patient.pk),
            "birth_date": patient.birth_date,
            "consent_accepted": patient.legal_terms_accepted,
            "registration_date": patient.registration_date,
        },
        "assigned_therapists": [
            {
                "specialty": link.therapist.specialty,
                "relationship_created_at": link.created_at,
            }
            for link in assigned_therapists
        ],
        "entry": {
            "id": str(entry.pk),
            "created_at": entry.created_at,
            "updated_at": entry.updated_at,
            "content": strip_tags(entry.content or "").strip(),
            "therapist_question": entry.therapist_question.question if entry.therapist_question else "",
        },
        "previous_analyses": [
            {
                "entry_created_at": analysis.entry.created_at,
                "primary_emotion": analysis.primary_emotion,
                "risk_level": analysis.risk_level,
                "emotions": analysis.emotions,
                "therapist_correction": analysis.therapist_correction,
            }
            for analysis in previous_analyses
        ],
    }


def _normalize_analysis_payload(payload):
    emotions = []
    for item in payload.get("emotions", []):
        emotion = str(item.get("emotion", "")).strip()
        if not emotion:
            continue
        percentage = max(0, min(100, float(item.get("percentage") or 0)))
        emotions.append({"emotion": emotion, "percentage": round(percentage, 2)})

    if not emotions:
        raise AnalysisServiceError("OpenAI no ha retornat emocions detectades.")

    emotions = sorted(emotions, key=lambda item: item["percentage"], reverse=True)
    risk_level = payload.get("risk_level", EmotionalAnalysis.LOW)
    if risk_level not in dict(EmotionalAnalysis.RISK_CHOICES):
        risk_level = EmotionalAnalysis.LOW

    return {
        "emotions": emotions,
        "primary_emotion": payload.get("primary_emotion") or emotions[0]["emotion"],
        "risk_level": risk_level,
        "summary": payload.get("summary", "").strip() or "Anàlisi generada sense resum disponible.",
        "recommendations": [
            str(recommendation).strip()
            for recommendation in payload.get("recommendations", [])
            if str(recommendation).strip()
        ],
    }
