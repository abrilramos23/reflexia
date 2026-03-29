import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    registration_date = models.DateTimeField(default=timezone.now)
    two_factor_enabled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return f"{self.first_name} {self.last_name} <{self.email}>"


class Patient(User):
    user_ptr = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        parent_link=True,
        primary_key=True,
        db_column="id",
        related_name="patient_profile",
    )
    birth_date = models.DateField()
    consent_accepted = models.BooleanField(default=False)
    consent_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "patient"
        verbose_name_plural = "patients"


class Therapist(User):
    user_ptr = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        parent_link=True,
        primary_key=True,
        db_column="id",
        related_name="therapist_profile",
    )
    license_number = models.CharField(max_length=100, unique=True)
    specialty = models.CharField(max_length=150)

    class Meta:
        verbose_name = "therapist"
        verbose_name_plural = "therapists"


class TherapistPatient(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="therapist_links",
    )
    therapist = models.ForeignKey(
        Therapist,
        on_delete=models.CASCADE,
        related_name="patient_links",
    )

    class Meta:
        verbose_name = "therapist-patient relationship"
        verbose_name_plural = "therapist-patient relationships"
        constraints = [
            models.UniqueConstraint(
                fields=("patient", "therapist"),
                name="unique_patient_therapist_relationship",
            )
        ]


class ProfessionalDirectoryEntry(models.Model):
    license_number = models.CharField(max_length=100, unique=True)
    complete_name = models.CharField(max_length=255)

    class Meta:
        verbose_name = "professional directory entry"
        verbose_name_plural = "professional directory entries"

    def __str__(self):
        return f"{self.license_number} - {self.complete_name}"
