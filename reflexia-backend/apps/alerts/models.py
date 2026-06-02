import uuid
from django.db import models
from django.utils import timezone

from apps.users.models import Patient, Therapist
from apps.entries.models import JournalEntry
from apps.analysis.models import EmotionalAnalysis
from apps.contacts.models import AssociatedContact


class Alert(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        VALIDATED = "validated", "Validated"
        DISMISSED = "dismissed", "Dismissed"

    class NotificationStatus(models.TextChoices):
        NOT_NOTIFIED = "not_notified", "Not notified"
        NOTIFIED = "notified", "Notified"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    emotional_analysis = models.OneToOneField(
        EmotionalAnalysis,
        on_delete=models.CASCADE,
        related_name="alert",
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="alerts",
    )
    risk_level = models.CharField(
        max_length=20,
        choices=EmotionalAnalysis.RISK_CHOICES,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    validating_therapist = models.ForeignKey(
        Therapist,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="validated_alerts",
    )
    validation_note = models.TextField(blank=True)
    justification = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    validated_at = models.DateTimeField(null=True, blank=True)
    escalation_level = models.IntegerField(default=0)
    last_escalation_at = models.DateTimeField(null=True, blank=True)
    notification_status = models.CharField(
        max_length=20,
        choices=NotificationStatus.choices,
        default=NotificationStatus.NOT_NOTIFIED,
    )
    last_notified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "alert"
        verbose_name_plural = "alerts"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("patient", "-created_at")),
            models.Index(fields=("status", "-created_at")),
        ]

    def __str__(self):
        return f"Alert {self.id} for {self.patient} (risk: {self.risk_level})"


class AlertNotification(models.Model):
    class Method(models.TextChoices):
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"

    class Status(models.TextChoices):
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert = models.ForeignKey(
        Alert,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    contact = models.ForeignKey(
        AssociatedContact,
        on_delete=models.CASCADE,
        related_name="alert_notifications",
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    method = models.CharField(
        max_length=20,
        choices=Method.choices,
        default=Method.EMAIL,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
    )
    recipient_email = models.EmailField()
    error_message = models.TextField(blank=True)

    class Meta:
        verbose_name = "alert notification"
        verbose_name_plural = "alert notifications"
        ordering = ("-sent_at",)
        indexes = [
            models.Index(fields=("alert", "-sent_at")),
            models.Index(fields=("status",)),
        ]

    def __str__(self):
        return f"Notification {self.id} for alert {self.alert_id} to {self.recipient_email}"
