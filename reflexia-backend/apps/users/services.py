from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import transaction
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.users.models import Patient, Therapist, TherapistPatient


@transaction.atomic
def register_therapist(*, first_name, last_name, email, password, license_number, specialty):
    validate_password(password)

    therapist = Therapist.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        license_number=license_number,
        specialty=specialty,
    )
    return therapist


@transaction.atomic
def register_patient(
    *,
    therapist,
    first_name,
    last_name,
    email,
    birth_date,
    consent_accepted=False,
    consent_date=None,
):
    patient = Patient(
        first_name=first_name,
        last_name=last_name,
        email=email,
        birth_date=birth_date,
        consent_accepted=consent_accepted,
        consent_date=consent_date,
        is_active=False,
    )
    patient.set_unusable_password()
    patient.save()
    TherapistPatient.objects.create(patient=patient, therapist=therapist)
    activation_url = build_patient_activation_url(patient)
    send_patient_activation_email(patient=patient, therapist=therapist, activation_url=activation_url)
    return patient, activation_url


def build_patient_activation_url(patient):
    uid = urlsafe_base64_encode(force_bytes(patient.pk))
    token = default_token_generator.make_token(patient)
    return f"{settings.FRONTEND_URL.rstrip('/')}/activate-account?uid={uid}&token={token}"


def send_patient_activation_email(*, patient, therapist, activation_url):
    subject = "Activate your Reflexia account"
    message = (
        f"Hello {patient.first_name},\n\n"
        f"{therapist.first_name} {therapist.last_name} has created your Reflexia account.\n"
        f"Use the following link to set your password and activate your access:\n\n"
        f"{activation_url}\n\n"
        "If you were not expecting this email, you can ignore it."
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [patient.email],
        fail_silently=False,
    )


@transaction.atomic
def activate_patient_account(*, patient, password):
    validate_password(password, user=patient)
    patient.set_password(password)
    patient.is_active = True
    patient.save(update_fields=["password", "is_active"])
    return patient
