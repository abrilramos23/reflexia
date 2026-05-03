import uuid

from django.db import models

from apps.users.models import Patient, Therapist


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


class JournalEntry(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_ANALYZED = "analyzed"
    STATUS_CHOICES = (
        (STATUS_DRAFT, "Draft"),
        (STATUS_ANALYZED, "Analyzed"),
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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-updated_at",)
        verbose_name = "journal entry"
        verbose_name_plural = "journal entries"

    def __str__(self):
        return f"{self.patient.email} - {self.created_at.isoformat()}"
