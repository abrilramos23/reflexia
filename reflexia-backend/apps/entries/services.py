from django.utils import timezone

from apps.entries.models import JournalEntry


DELETED_ENTRY_PLACEHOLDER = "Aquesta entrada ha estat eliminada i anonimitzada."


def soft_delete_entry(*, entry):
    if entry.deleted_at is not None:
        return entry

    entry.content = DELETED_ENTRY_PLACEHOLDER
    entry.deleted_at = timezone.now()
    entry.therapist_question = None
    entry.status = JournalEntry.STATUS_DRAFT
    entry.save(
        update_fields=[
            "content",
            "deleted_at",
            "therapist_question",
            "status",
            "updated_at",
        ]
    )
    if hasattr(entry, "analysis"):
        entry.analysis.delete()
    return entry
