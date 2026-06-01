import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.users.models import Patient, Therapist


class AssociatedContact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    email = models.EmailField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    relation = models.CharField(max_length=100)

    class Meta:
        verbose_name = "associated contact"
        verbose_name_plural = "associated contacts"
        ordering = ("name",)
        constraints = [
            models.CheckConstraint(
                check=(
                    (models.Q(email__isnull=False) & ~models.Q(email=""))
                    | (models.Q(phone__isnull=False) & ~models.Q(phone=""))
                ),
                name="associated_contact_requires_email_or_phone",
            )
        ]

    def clean(self):
        if not self.email and not self.phone:
            raise ValidationError("Cal indicar com a mínim un mètode de contacte.")


class DefaultContact(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="default_contact_links",
    )
    contact = models.ForeignKey(
        AssociatedContact,
        on_delete=models.CASCADE,
        related_name="patient_links",
    )
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name = "patient-associated contact relationship"
        verbose_name_plural = "patient-associated contact relationships"
        constraints = [
            models.UniqueConstraint(
                fields=("patient", "contact"),
                name="unique_patient_contact_relationship",
            )
        ]


class SupportTherapist(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    therapist = models.ForeignKey(
        Therapist,
        on_delete=models.CASCADE,
        related_name="support_therapist_links",
    )
    support = models.ForeignKey(
        Therapist,
        on_delete=models.CASCADE,
        related_name="supported_by_links",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    requested_at = models.DateTimeField(default=timezone.now)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "support therapist relationship"
        verbose_name_plural = "support therapist relationships"
        ordering = ("-requested_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("therapist", "support"),
                name="unique_support_therapist_relationship",
            ),
            models.CheckConstraint(
                check=~models.Q(therapist=models.F("support")),
                name="support_therapist_cannot_match_therapist",
            )
        ]

    def clean(self):
        if self.therapist_id == self.support_id:
            raise ValidationError("Un terapeuta no pot ser el seu propi terapeuta de suport.")

    def accept(self):
        self.status = self.Status.ACCEPTED
        self.responded_at = timezone.now()
        self.save(update_fields=["status", "responded_at"])
        return self

    def reject(self):
        self.status = self.Status.REJECTED
        self.responded_at = timezone.now()
        self.save(update_fields=["status", "responded_at"])
        return self
