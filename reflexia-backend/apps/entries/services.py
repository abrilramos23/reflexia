from collections import Counter
from html import escape, unescape
from io import BytesIO

from django.utils import timezone
from django.utils.html import strip_tags
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from apps.entries.models import JournalEntry


DELETED_ENTRY_PLACEHOLDER = "Aquesta entrada ha estat eliminada i anonimitzada."
ENTRY_DELETION_EXPLANATION = (
    "Per obligació legal de conservació de la documentació clínica, l'entrada es deixa de mostrar "
    "per al pacient però es mantindrà anonimitzada durant el termini mínim de retenció. "
    "Si necessites més informació, pots exercir el teu dret d'accés i demanar-la al centre o al teu terapeuta."
)


def compute_entry_retention_date(*, reference_date=None):
    return (reference_date or timezone.now()) + timezone.timedelta(days=365 * 5)


def soft_delete_entry(*, entry):
    if entry.is_deleted:
        return entry

    now = timezone.now()
    entry.content = DELETED_ENTRY_PLACEHOLDER
    entry.deleted_at = now
    entry.therapist_question = None
    entry.status = JournalEntry.STATUS_DELETED
    entry.retention_date = max(entry.retention_date, compute_entry_retention_date(reference_date=now))
    entry.save(
        update_fields=[
            "content",
            "deleted_at",
            "therapist_question",
            "status",
            "retention_date",
            "updated_at",
        ]
    )
    if hasattr(entry, "analysis"):
        entry.analysis.delete()
    return entry


def build_export_filename(*, prefix, suffix=None):
    safe_prefix = prefix.replace(" ", "-").lower()
    safe_suffix = f"-{suffix}" if suffix else ""
    timestamp = timezone.now().strftime("%Y%m%d-%H%M%S")
    return f"{safe_prefix}{safe_suffix}-{timestamp}.pdf"


def render_entries_pdf(*, title, entries):
    entries = list(entries)
    generated_at = timezone.localtime(timezone.now())
    patient = entries[0].patient if entries else None
    document_title = _build_document_title(title=title, entries=entries, patient=patient)
    styles = _build_pdf_styles()
    story = []

    _append_cover(
        story,
        styles=styles,
        title=document_title,
        source_title=title,
        entries=entries,
        patient=patient,
        generated_at=generated_at,
    )

    if entries:
        story.append(PageBreak())
        story.append(Paragraph("Entrades exportades", styles["SectionTitle"]))
        story.append(Spacer(1, 0.25 * cm))
        for index, entry in enumerate(entries, start=1):
            _append_entry(story, styles=styles, entry=entry, index=index, total=len(entries))
    else:
        story.append(Spacer(1, 0.35 * cm))
        story.append(_empty_state_table("No hi ha entrades visibles per exportar.", styles))

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title=document_title,
        author="Reflexia",
        creator="Reflexia",
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=2.25 * cm,
        bottomMargin=1.8 * cm,
    )
    document.build(
        story,
        onFirstPage=_draw_page_frame(document_title=document_title),
        onLaterPages=_draw_page_frame(document_title=document_title),
    )
    return buffer.getvalue()


def _append_cover(story, *, styles, title, source_title, entries, patient, generated_at):
    story.append(Spacer(1, 0.18 * cm))
    story.append(Paragraph(title, styles["Title"]))
    story.append(Spacer(1, 0.25 * cm))
    story.append(
        Paragraph(
            "Exportació de dades de journaling generada des de Reflexia. "
            "Aquest document recull la informació visible en el moment de la descàrrega.",
            styles["Lead"],
        )
    )
    story.append(Spacer(1, 0.65 * cm))

    story.append(Paragraph("Resum del document", styles["SectionTitle"]))
    story.append(Spacer(1, 0.25 * cm))
    story.append(
        _metadata_table(
            [
                ("Tipus d'exportació", source_title),
                ("Pacient", _format_person_name(patient) if patient else "No disponible"),
                ("Entrades incloses", str(len(entries))),
                ("Període", _format_entries_period(entries)),
                ("Generat", generated_at.strftime("%d/%m/%Y %H:%M")),
                ("Nivell de risc més alt", _format_highest_risk(entries)),
            ],
            styles,
        )
    )

def _append_entry(story, *, styles, entry, index, total):
    analysis = getattr(entry, "analysis", None)
    question = getattr(entry, "therapist_question", None)
    created_at = timezone.localtime(entry.created_at).strftime("%d/%m/%Y %H:%M")
    updated_at = timezone.localtime(entry.updated_at).strftime("%d/%m/%Y %H:%M")
    risk_level = getattr(analysis, "risk_level", None)
    risk_label = _format_risk_level(risk_level)

    header_block = [
        HRFlowable(width="100%", color=colors.HexColor("#d6e0dc"), thickness=0.8, spaceAfter=0.35 * cm),
        _entry_heading_table(
            title=f"Entrada {index} de {total}",
            subtitle=f"Creada el {created_at}",
            badge=risk_label,
            risk_level=risk_level,
            styles=styles,
        ),
        Spacer(1, 0.25 * cm),
        _metadata_table(
            [
                ("Estat", _format_entry_status(entry.status)),
                ("Última actualització", updated_at),
                ("Pregunta terapèutica", question.question if question else "Sense pregunta associada"),
                ("Emoció principal", getattr(analysis, "primary_emotion", "") or "Sense anàlisi"),
            ],
            styles,
            compact=True,
        ),
        Spacer(1, 0.28 * cm),
        Paragraph("Text de l'entrada", styles["SmallLabel"]),
    ]

    story.append(KeepTogether(header_block))
    story.append(Spacer(1, 0.1 * cm))
    story.append(_text_box(_plain_text(entry.content) or "Sense contingut", styles))
    story.append(Spacer(1, 0.25 * cm))

    if analysis:
        story.extend(_analysis_block(analysis, styles))

    story.append(Spacer(1, 0.45 * cm))


def _analysis_block(analysis, styles):
    elements = [Spacer(1, 0.25 * cm), Paragraph("Anàlisi emocional", styles["SmallLabel"])]
    if analysis.summary:
        elements.append(Paragraph(_paragraph_text(analysis.summary), styles["Body"]))

    emotion_summary = _format_emotions(getattr(analysis, "emotions", None))
    if emotion_summary:
        elements.append(Paragraph(f"Emocions detectades: {_paragraph_text(emotion_summary)}", styles["Muted"]))

    recommendations = [item for item in getattr(analysis, "recommendations", []) if item]
    if recommendations:
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(Paragraph("Recomanacions", styles["SmallLabel"]))
        for item in recommendations:
            elements.append(Paragraph(f"- {_paragraph_text(item)}", styles["Body"]))

    return elements


def _metadata_table(items, styles, *, compact=False):
    rows = []
    for index in range(0, len(items), 2):
        row_items = items[index:index + 2]
        row = []
        for label, value in row_items:
            row.append(_metadata_cell(label, value, styles))
        if len(row) == 1:
            row.append("")
        rows.append(row)

    table = Table(rows, colWidths=[8.1 * cm, 8.1 * cm], hAlign="LEFT")
    vertical_padding = 6 if compact else 8
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f6f8f7")),
                ("BOX", (0, 0), (-1, -1), 0.55, colors.HexColor("#d6e0dc")),
                ("INNERGRID", (0, 0), (-1, -1), 0.55, colors.HexColor("#d6e0dc")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), vertical_padding),
                ("BOTTOMPADDING", (0, 0), (-1, -1), vertical_padding),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return table


def _metadata_cell(label, value, styles):
    return [
        Paragraph(_paragraph_text(label.upper()), styles["MetaLabel"]),
        Spacer(1, 0.04 * cm),
        Paragraph(_paragraph_text(value), styles["MetaValue"]),
    ]


def _entry_heading_table(*, title, subtitle, badge, risk_level, styles):
    table = Table(
        [
            [
                [Paragraph(_paragraph_text(title), styles["EntryTitle"]), Paragraph(_paragraph_text(subtitle), styles["Muted"])],
                Paragraph(_paragraph_text(badge), styles["RiskBadge"]),
            ]
        ],
        colWidths=[12.6 * cm, 3.6 * cm],
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (1, 0), (1, 0), _risk_background(risk_level)),
                ("TEXTCOLOR", (1, 0), (1, 0), _risk_color(risk_level)),
                ("BOX", (1, 0), (1, 0), 0.1, _risk_background(risk_level)),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (0, 0), 0),
                ("RIGHTPADDING", (0, 0), (0, 0), 8),
                ("TOPPADDING", (1, 0), (1, 0), 6),
                ("BOTTOMPADDING", (1, 0), (1, 0), 6),
            ]
        )
    )
    return table


def _text_box(text, styles):
    return Paragraph(_paragraph_text(text), styles["Muted"])


def _empty_state_table(text, styles):
    table = Table([[Paragraph(_paragraph_text(text), styles["Muted"])]], colWidths=[16.2 * cm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f6f8f7")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#d6e0dc")),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    return table


def _draw_page_frame(*, document_title):
    def draw(canvas, document):
        canvas.saveState()
        width, height = A4

        canvas.setFillColor(colors.HexColor("#14342b"))
        canvas.rect(0, height - 1.12 * cm, width, 1.12 * cm, fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor("#3f8f78"))
        canvas.rect(0, height - 1.22 * cm, width, 0.1 * cm, fill=1, stroke=0)

        canvas.setFont("Helvetica-Bold", 10)
        canvas.setFillColor(colors.white)
        canvas.drawString(1.8 * cm, height - 0.72 * cm, "Reflexia")

        canvas.setStrokeColor(colors.HexColor("#d6e0dc"))
        canvas.setLineWidth(0.55)
        canvas.line(1.8 * cm, 1.25 * cm, width - 1.8 * cm, 1.25 * cm)

        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#6a7d75"))
        canvas.drawString(1.8 * cm, 0.78 * cm, "Document generat automàticament per Reflexia")
        canvas.drawRightString(width - 1.8 * cm, 0.78 * cm, f"Pàgina {document.page}")

        canvas.setTitle(document_title)
        canvas.setAuthor("Reflexia")
        canvas.setCreator("Reflexia")
        canvas.restoreState()

    return draw


def _build_pdf_styles():
    base_styles = getSampleStyleSheet()
    return {
        "Brand": ParagraphStyle(
            "Brand",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#3f6f61"),
            spaceAfter=0,
        ),
        "Title": ParagraphStyle(
            "Title",
            parent=base_styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=27,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#14342b"),
            spaceAfter=0,
        ),
        "Lead": ParagraphStyle(
            "Lead",
            parent=base_styles["BodyText"],
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            textColor=colors.HexColor("#1f302a"),
            alignment=TA_CENTER,
        ),
        "SectionTitle": ParagraphStyle(
            "SectionTitle",
            parent=base_styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#14342b"),
            spaceAfter=4,
        ),
        "EntryTitle": ParagraphStyle(
            "EntryTitle",
            parent=base_styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=17,
            textColor=colors.HexColor("#14342b"),
            spaceAfter=2,
        ),
        "SmallLabel": ParagraphStyle(
            "SmallLabel",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#3f6f61"),
            spaceAfter=4,
        ),
        "MetaLabel": ParagraphStyle(
            "MetaLabel",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#6a7d75"),
        ),
        "MetaValue": ParagraphStyle(
            "MetaValue",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=12,
            textColor=colors.HexColor("#1d3029"),
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base_styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#20322c"),
        ),
        "TextBox": ParagraphStyle(
            "TextBox",
            parent=base_styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#20322c"),
            backColor=colors.HexColor("#fbfcfb"),
            borderColor=colors.HexColor("#d6e0dc"),
            borderWidth=0.6,
            borderPadding=10,
            spaceAfter=0,
        ),
        "Muted": ParagraphStyle(
            "Muted",
            parent=base_styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#61746d"),
        ),
        "RiskBadge": ParagraphStyle(
            "RiskBadge",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#52635c"),
        ),
    }


def _build_document_title(*, title, entries, patient):
    patient_name = _format_person_name(patient) if patient else "Pacient"
    if len(entries) == 1:
        created_at = timezone.localtime(entries[0].created_at).strftime("%d/%m/%Y")
        return f"Entrada de journaling de {patient_name} - {created_at}"
    if len(entries) > 1:
        return f"Historial de journaling de {patient_name}"
    return title


def _format_person_name(person):
    if not person:
        return "No disponible"
    name = f"{getattr(person, 'first_name', '')} {getattr(person, 'last_name', '')}".strip()
    return name or getattr(person, "email", "No disponible")


def _format_entries_period(entries):
    if not entries:
        return "Sense entrades"
    dates = [timezone.localtime(entry.created_at) for entry in entries]
    first_date = min(dates).strftime("%d/%m/%Y")
    last_date = max(dates).strftime("%d/%m/%Y")
    if first_date == last_date:
        return first_date
    return f"{first_date} - {last_date}"


def _risk_distribution(entries):
    counts = Counter(
        _format_risk_level(getattr(getattr(entry, "analysis", None), "risk_level", None))
        for entry in entries
    )
    counts.pop("Sense anàlisi", None)
    order = ["Alt", "Moderat", "Baix", "Cap"]
    return [(label, counts[label]) for label in order if counts[label]]


def _format_highest_risk(entries):
    rank = {"high": 4, "moderate": 3, "low": 2, "none": 1}
    risk_levels = [
        getattr(getattr(entry, "analysis", None), "risk_level", None)
        for entry in entries
        if getattr(getattr(entry, "analysis", None), "risk_level", None)
    ]
    if not risk_levels:
        return "Sense anàlisi"
    return _format_risk_level(max(risk_levels, key=lambda risk: rank.get(risk, 0)))


def _format_risk_level(risk_level):
    labels = {
        "none": "Cap",
        "low": "Baix",
        "moderate": "Moderat",
        "high": "Alt",
    }
    return labels.get(risk_level, "Sense anàlisi")


def _risk_background(risk_level):
    return {
        "none": colors.HexColor("#edf2f0"),
        "low": colors.HexColor("#e5f4ec"),
        "moderate": colors.HexColor("#fff4d8"),
        "high": colors.HexColor("#fde8e8"),
    }.get(risk_level, colors.HexColor("#edf2f0"))


def _risk_color(risk_level):
    return {
        "none": colors.HexColor("#52635c"),
        "low": colors.HexColor("#276749"),
        "moderate": colors.HexColor("#8a5a00"),
        "high": colors.HexColor("#9b1c1c"),
    }.get(risk_level, colors.HexColor("#52635c"))


def _format_entry_status(status):
    return {
        JournalEntry.STATUS_ACTIVE: "Activa",
        JournalEntry.STATUS_MODIFIED: "Modificada",
        JournalEntry.STATUS_DELETED: "Eliminada",
    }.get(status, status or "No disponible")


def _format_emotions(emotions):
    if not emotions:
        return ""
    formatted = []
    for item in emotions[:5]:
        if isinstance(item, dict):
            emotion = item.get("emotion") or item.get("name")
            percentage = item.get("percentage")
            if emotion and percentage is not None:
                formatted.append(f"{emotion} ({percentage}%)")
            elif emotion:
                formatted.append(str(emotion))
        elif item:
            formatted.append(str(item))
    return ", ".join(formatted)


def _plain_text(value):
    return unescape(strip_tags(value or "")).strip()


def _paragraph_text(value):
    return escape(str(value or "")).replace("\n", "<br/>")
