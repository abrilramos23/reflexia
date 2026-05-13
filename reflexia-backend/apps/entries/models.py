import uuid

from django.db import models
from django.utils import timezone

from apps.users.models import Patient, Therapist


def default_entry_retention_date():
    return timezone.now() + timezone.timedelta(days=365 * 5)


class TherapistQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    therapist = models.ForeignKey(
        Therapist,
        on_delete=models.CASCADE,
        related_name="journal_questions",
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="active_journal_questions",
    )
    question = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "therapist question"
        verbose_name_plural = "therapist questions"

    def __str__(self):
        return f"Question for {self.patient.email}"

    @property
    def text(self):
        return self.question

    @property
    def creation_date(self):
        return self.created_at

    @property
    def resolved(self):
        return not self.is_active


class JournalEntry(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_MODIFIED = "modified"
    STATUS_DELETED = "deleted"
    STATUS_CHOICES = (
        (STATUS_ACTIVE, "Active"),
        (STATUS_MODIFIED, "Modified"),
        (STATUS_DELETED, "Deleted"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="journal_entries",
    )
    therapist_question = models.ForeignKey(
        TherapistQuestion,
        on_delete=models.SET_NULL,
        related_name="entries",
        null=True,
        blank=True,
    )
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    retention_date = models.DateTimeField(default=default_entry_retention_date)

    class Meta:
        ordering = ("-updated_at",)
        verbose_name = "journal entry"
        verbose_name_plural = "journal entries"

    def __str__(self):
        return f"{self.patient.email} - {self.created_at.isoformat()}"

    @property
    def creation_date(self):
        return self.created_at

    @property
    def modification_date(self):
        if not self.updated_at or not self.created_at:
            return None
        if (self.updated_at - self.created_at) <= timezone.timedelta(seconds=1):
            return None
        return self.updated_at

    @property
    def question(self):
        return self.therapist_question

    @property
    def is_deleted(self):
        return self.status == self.STATUS_DELETED or self.deleted_at is not None


class PrivateNote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    therapist = models.ForeignKey(
        Therapist,
        on_delete=models.CASCADE,
        related_name="private_entry_notes",
    )
    entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name="private_notes",
    )
    content = models.TextField()
    creation_date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-creation_date",)
        verbose_name = "private note"
        verbose_name_plural = "private notes"

    def __str__(self):
        return f"Private note for {self.entry_id}"
