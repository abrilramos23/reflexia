from django.utils import timezone

from apps.entries.models import EmotionalAnalysis, JournalEntry


DELETED_ENTRY_PLACEHOLDER = "Aquesta entrada ha estat eliminada i anonimitzada."


def soft_delete_entry(*, entry):
    if entry.deleted_at is not None:
        return entry

    entry.content = DELETED_ENTRY_PLACEHOLDER
    entry.deleted_at = timezone.now()
    entry.last_analyzed_at = None
    entry.therapist_question = None
    entry.status = JournalEntry.STATUS_DRAFT
    entry.save(
        update_fields=[
            "content",
            "deleted_at",
            "last_analyzed_at",
            "therapist_question",
            "status",
            "updated_at",
        ]
    )
    EmotionalAnalysis.objects.filter(entry=entry).delete()
    return entry
