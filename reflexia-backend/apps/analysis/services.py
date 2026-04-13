import re
from django.utils.html import strip_tags


DISCLAIMER_TEXT = (
    "Aquesta anàlisi és orientativa, s’ha generat automàticament i serà revisada pel teu terapeuta."
)


EMOTION_RULES = (
    ("angoixa", ("angoixa", "ansietat", "angoixa", "nervis", "sobrepassat", "ofegat")),
    ("tristesa", ("trist", "trista", "tristor", "sol", "sola", "buit", "plorar")),
    ("calma", ("calmat", "calmada", "tranquil", "tranquila", "pau", "serenor")),
    ("frustracio", ("frustrat", "frustrada", "rabia", "ràbia", "enfadat", "enfadada")),
    ("esperanca", ("esperanca", "esperança", "il·lusio", "il·lusió", "optimista")),
)


NEGATIVE_MARKERS = (
    "malament",
    "pitjor",
    "ansietat",
    "angoixa",
    "trist",
    "trista",
    "cansat",
    "cansada",
    "bloquejat",
    "bloquejada",
    "sol",
    "sola",
)

POSITIVE_MARKERS = (
    "be",
    "bé",
    "millor",
    "tranquil",
    "tranquila",
    "agrait",
    "agraida",
    "agraïda",
    "content",
    "contenta",
    "esperanca",
    "esperança",
)


def anonymize_entry_content(*, content, patient=None, therapist=None):
    anonymized = strip_tags(content).strip()

    if not anonymized:
        return ""

    sensitive_tokens = {
        patient.email if patient else "",
        getattr(patient, "first_name", ""),
        getattr(patient, "last_name", ""),
        f"{getattr(patient, 'first_name', '')} {getattr(patient, 'last_name', '')}".strip(),
        therapist.email if therapist else "",
        getattr(therapist, "first_name", ""),
        getattr(therapist, "last_name", ""),
        f"{getattr(therapist, 'first_name', '')} {getattr(therapist, 'last_name', '')}".strip(),
    }

    for token in sensitive_tokens:
        cleaned = token.strip()
        if len(cleaned) < 3:
          continue
        anonymized = re.sub(re.escape(cleaned), "[anonimitzat]", anonymized, flags=re.IGNORECASE)

    anonymized = re.sub(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", "[email]", anonymized)
    anonymized = re.sub(r"\b(?:\+?\d[\d\s().-]{7,}\d)\b", "[telefon]", anonymized)
    anonymized = re.sub(r"https?://\S+", "[url]", anonymized)

    return anonymized


def build_emotional_analysis(*, anonymized_content):
    normalized = anonymized_content.lower()

    emotion_scores = {}
    for emotion, keywords in EMOTION_RULES:
        emotion_scores[emotion] = sum(keyword in normalized for keyword in keywords)

    primary_emotion = max(emotion_scores, key=emotion_scores.get, default="mixt")
    if emotion_scores.get(primary_emotion, 0) == 0:
        primary_emotion = "mixt"

    positive_hits = sum(marker in normalized for marker in POSITIVE_MARKERS)
    negative_hits = sum(marker in normalized for marker in NEGATIVE_MARKERS)

    if negative_hits > positive_hits:
        tone = "delicat"
    elif positive_hits > negative_hits:
        tone = "constructiu"
    else:
        tone = "mixt"

    short_excerpt = anonymized_content[:180].strip()
    if len(anonymized_content) > 180:
        short_excerpt = f"{short_excerpt}..."

    if not short_excerpt:
        short_excerpt = "No s’ha pogut extreure prou contingut per resumir l’entrada."

    summary = f"L’entrada descriu un estat {tone} amb predomini de {primary_emotion}. Fragment observat: {short_excerpt}"

    return {
        "summary": summary,
        "primary_emotion": primary_emotion,
        "tone": tone,
        "disclaimer": DISCLAIMER_TEXT,
    }