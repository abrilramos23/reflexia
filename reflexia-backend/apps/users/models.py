import uuid
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

class Organisation(models.Model):
    class Type(models.TextChoices):
        CLINIC     = 'clinic',     'Clinic'
        INDIVIDUAL = 'individual', 'Individual'

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name       = models.CharField(max_length=255)
    type       = models.CharField(max_length=20, choices=Type.choices)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'organisation'
        verbose_name_plural = 'organisations'

    def __str__(self):
        return f"{self.name} ({self.type})"


"""
class Subscription(models.Model):
    class Plan(models.TextChoices):
        FREE   = 'free',   'Free'
        PRO    = 'pro',    'Pro'
        CLINIC = 'clinic', 'Clinic'

    class Status(models.TextChoices):
        ACTIVE   = 'active',   'Active'
        CANCELED = 'canceled', 'Canceled'

    class Periodicity(models.TextChoices):
        MONTHLY = 'monthly', 'Monthly'
        YEARLY  = 'yearly',  'Yearly'

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan         = models.CharField(max_length=20, choices=Plan.choices, default=Plan.FREE)
    status       = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    periodicity  = models.CharField(max_length=20, choices=Periodicity.choices, default=Periodicity.MONTHLY)
    ini_date     = models.DateTimeField(default=timezone.now)
    end_date     = models.DateTimeField(null=True, blank=True)
    organisation = models.ForeignKey(
                       Organisation,
                       on_delete=models.CASCADE,
                       related_name='subscriptions',
                       null=True, blank=True
                   )

    class Meta:
        verbose_name = 'subscription'
        verbose_name_plural = 'subscriptions'

    def __str__(self):
        return f"Sub: {self.plan} - {self.organisation.name if self.organisation else 'No Org'}"
"""


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
        extra_fields.setdefault("role", User.Role.PLATFORM_ADMIN)
        return self.create_user(email, password, **extra_fields)


class TherapistManager(UserManager):
    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.THERAPIST)
        return super().create_user(email, password, **extra_fields)


class PatientManager(UserManager):
    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.PATIENT)
        return super().create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        PLATFORM_ADMIN = 'platform_admin', 'Platform Admin'
        THERAPIST      = 'therapist',      'Therapist'
        PATIENT        = 'patient',        'Patient'

    id                       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name               = models.CharField(max_length=100)
    last_name                = models.CharField(max_length=150)
    email                    = models.EmailField(unique=True)
    role                     = models.CharField(max_length=20, choices=Role.choices, default=Role.PATIENT)
    
    organisations            = models.ManyToManyField(
                                    Organisation,
                                    through='OrganisationMember',
                                    related_name='members'
                                )
    
    registration_date        = models.DateTimeField(default=timezone.now)
    two_factor_enabled       = models.BooleanField(default=False)
    two_factor_secret        = models.CharField(max_length=64, blank=True)
    two_factor_pending_secret= models.CharField(max_length=64, blank=True)
    is_active                = models.BooleanField(default=True)
    is_staff                 = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return f"{self.first_name} {self.last_name} <{self.email}>"

    @property
    def is_platform_admin(self):
        return self.role == self.Role.PLATFORM_ADMIN

    @property
    def is_clinic_admin(self):
        return self.organisation_memberships.filter(is_admin=True).exists()

    @property
    def organisation(self):
        membership = self.organisation_memberships.select_related("organisation").first()
        return membership.organisation if membership else None

    @property
    def is_therapist(self):
        return self.role == self.Role.THERAPIST

    @property
    def is_patient(self):
        return self.role == self.Role.PATIENT


class OrganisationMember(models.Model):
    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organisation_memberships')
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='user_memberships')
    is_admin     = models.BooleanField(default=False)
    joined_at    = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'organisation')
        constraints = [
            models.UniqueConstraint(
                fields=("user",),
                name="unique_organisation_membership_per_user",
            ),
        ]
        verbose_name = 'organisation member'
        verbose_name_plural = 'organisation members'

    def clean(self):
        if self.user.role != User.Role.THERAPIST:
            raise ValidationError(
                "Només els usuaris amb el rol de terapeuta poden ser membres d'una organització."
            )
        if self.pk:
            old_instance = OrganisationMember.objects.get(pk=self.pk)
            if old_instance.is_admin and not self.is_admin:
                admin_count = OrganisationMember.objects.filter(
                    organisation=self.organisation, 
                    is_admin=True
                ).count()
                if admin_count <= 1:
                    raise ValidationError(
                        "No es pot treure el permís d'administrador perquè ets l'únic administrador d'aquesta organització."
                    )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.is_admin:
            admin_count = OrganisationMember.objects.filter(
                organisation=self.organisation, 
                is_admin=True
            ).count()
            if admin_count <= 1:
                member_count = OrganisationMember.objects.filter(organisation=self.organisation).count()
                if member_count > 1:
                    raise ValidationError(
                        "No es pot eliminar aquest membre perquè és l'únic administrador de l'organització."
                    )
        super().delete(*args, **kwargs)


class Therapist(User):
    user_ptr       = models.OneToOneField(
                         User,
                         on_delete=models.CASCADE,
                         parent_link=True,
                         primary_key=True,
                         db_column='id',
                         related_name='therapist_profile',
                     )
    license_number = models.CharField(max_length=100, unique=True)
    specialty      = models.CharField(max_length=150)

    objects = TherapistManager()

    class Meta:
        verbose_name = 'therapist'
        verbose_name_plural = 'therapists'


class Patient(User):
    user_ptr         = models.OneToOneField(
                           User,
                           on_delete=models.CASCADE,
                           parent_link=True,
                           primary_key=True,
                           db_column='id',
                           related_name='patient_profile',
                       )
    birth_date       = models.DateField()
    consent_accepted = models.BooleanField(default=False)
    consent_date     = models.DateTimeField(null=True, blank=True)

    objects = PatientManager()

    class Meta:
        verbose_name = 'patient'
        verbose_name_plural = 'patients'


class TherapistPatient(models.Model):
    therapist  = models.ForeignKey(
                     Therapist,
                     on_delete=models.CASCADE,
                     related_name='patient_links',
                 )
    patient    = models.ForeignKey(
                     Patient,
                     on_delete=models.CASCADE,
                     related_name='therapist_links',
                 )
    created_at = models.DateTimeField(default=timezone.now)
    is_active  = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'therapist-patient relationship'
        verbose_name_plural = 'therapist-patient relationships'
        constraints = [
            models.UniqueConstraint(
                fields=('therapist', 'patient'),
                name='unique_therapist_patient'
            )
        ]


class ProfessionalDirectoryEntry(models.Model):
    license_number = models.CharField(max_length=100, unique=True)
    complete_name  = models.CharField(max_length=255)

    class Meta:
        verbose_name = 'professional directory entry'
        verbose_name_plural = 'professional directory entries'

    def __str__(self):
        return f"{self.license_number} - {self.complete_name}"
