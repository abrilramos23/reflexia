from django.db import models
from django.utils import timezone

from apps.entries.models import JournalEntry


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

    entry = models.OneToOneField(
        JournalEntry,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="analysis",
    )
    emotions = models.JSONField(default=list)
    primary_emotion = models.CharField(max_length=80)
    risk_level = models.CharField(max_length=20, choices=RISK_CHOICES)
    summary = models.TextField()
    recommendations = models.JSONField(default=list, blank=True)
    analyzed_at = models.DateTimeField(default=timezone.now)
    reviewed_by_therapist = models.BooleanField(default=False)
    therapist_correction = models.TextField(blank=True)

    class Meta:
        ordering = ("-analyzed_at",)
        verbose_name = "emotional analysis"
        verbose_name_plural = "emotional analyses"

    def __str__(self):
        return f"Analysis for {self.entry_id} ({self.risk_level})"
