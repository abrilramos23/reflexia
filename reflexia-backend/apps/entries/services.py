import math
import textwrap

from django.utils import timezone
from django.utils.html import strip_tags

from apps.entries.models import JournalEntry


DELETED_ENTRY_PLACEHOLDER = "Aquesta entrada ha estat eliminada i anonimitzada."
ENTRY_DELETION_EXPLANATION = (
    "Per obligacio legal de conservacio de la documentacio clinica, l'entrada es deixa de mostrar "
    "per al pacient pero es mantindra anonimitzada durant el termini minim de retencio. "
    "Si necessites mes informacio, pots exercir el teu dret d'acces i demanar-la al centre o al teu terapeuta."
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
    lines = [title, "", f"Generat el {timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')}", ""]

    for index, entry in enumerate(entries, start=1):
        created_at = timezone.localtime(entry.created_at).strftime("%d/%m/%Y %H:%M")
        risk_level = getattr(getattr(entry, "analysis", None), "risk_level", "sense analisi")
        lines.extend(
            [
                f"Entrada {index}",
                f"Data de creacio: {created_at}",
                f"Nivell de risc: {risk_level}",
            ]
        )
        content_lines = _wrap_text(strip_tags(entry.content or "").strip() or "Sense contingut")
        lines.extend(content_lines)
        lines.extend(["", ""])

    page_size = 42
    pages = [lines[start:start + page_size] for start in range(0, len(lines), page_size)] or [["Sense dades"]]
    return _build_pdf_document(pages)


def _wrap_text(text):
    paragraphs = text.splitlines() or [text]
    wrapped_lines = []
    for paragraph in paragraphs:
        normalized_paragraph = " ".join(paragraph.split())
        if not normalized_paragraph:
            wrapped_lines.append("")
            continue
        wrapped_lines.extend(textwrap.wrap(normalized_paragraph, width=92) or [""])
    return wrapped_lines


def _build_pdf_document(pages):
    objects = []

    def add_object(raw_bytes):
        objects.append(raw_bytes)
        return len(objects)

    font_object_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    page_object_ids = []
    content_object_ids = []

    for page_lines in pages:
        stream = _build_page_stream(page_lines)
        content_object_id = add_object(
            f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1") + stream + b"\nendstream"
        )
        content_object_ids.append(content_object_id)
        page_object_ids.append(None)

    pages_object_id = add_object(b"<< /Type /Pages /Kids [] /Count 0 >>")

    for index, content_object_id in enumerate(content_object_ids):
        page_object_id = add_object(
            (
                f"<< /Type /Page /Parent {pages_object_id} 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 {font_object_id} 0 R >> >> "
                f"/Contents {content_object_id} 0 R >>"
            ).encode("latin-1")
        )
        page_object_ids[index] = page_object_id

    kids = " ".join(f"{page_id} 0 R" for page_id in page_object_ids)
    objects[pages_object_id - 1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_object_ids)} >>".encode("latin-1")
    catalog_object_id = add_object(f"<< /Type /Catalog /Pages {pages_object_id} 0 R >>".encode("latin-1"))

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]

    for object_id, raw_bytes in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{object_id} 0 obj\n".encode("latin-1"))
        pdf.extend(raw_bytes)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))

    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_object_id} 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF"
        ).encode("latin-1")
    )
    return bytes(pdf)


def _build_page_stream(page_lines):
    commands = ["BT", "/F1 12 Tf", "14 TL", "50 760 Td"]
    for line in page_lines:
        safe_line = _escape_pdf_text(line)
        commands.append(f"({safe_line}) Tj")
        commands.append("T*")
    commands.append("ET")
    return "\n".join(commands).encode("latin-1", errors="replace")


def _escape_pdf_text(text):
    normalized = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return normalized.encode("latin-1", errors="replace").decode("latin-1")
