import uuid

from django.db import models

from apps.entries.models import JournalEntry
from apps.users.models import Therapist


class EmotionalAnalysis(models.Model):
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    RISK_CHOICES = (
        (NONE, "None"),
        (LOW, "Low"),
        (MODERATE, "Moderate"),
        (HIGH, "High"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entry = models.OneToOneField(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name="analysis",
    )
    emotions = models.JSONField(default=list)
    primary_emotion = models.CharField(max_length=80)
    risk_level = models.CharField(max_length=20, choices=RISK_CHOICES)
    summary = models.TextField()
    tone = models.CharField(max_length=120, blank=True)
    key_themes = models.JSONField(default=list, blank=True)
    recommendations = models.JSONField(default=list, blank=True)
    model_name = models.CharField(max_length=120, blank=True)
    model_response_id = models.CharField(max_length=120, blank=True)
    raw_response = models.JSONField(default=dict, blank=True)
    therapist_correction = models.TextField(blank=True)
    corrected_by = models.ForeignKey(
        Therapist,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="analysis_corrections",
    )
    corrected_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)
        verbose_name = "emotional analysis"
        verbose_name_plural = "emotional analyses"

    def __str__(self):
        return f"Analysis for {self.entry_id} ({self.risk_level})"
