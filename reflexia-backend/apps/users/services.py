from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from urllib.parse import urlencode

from apps.users.models import (
    InvitacioOrganitzacio,
    Organisation,
    OrganisationMember,
    Patient,
    Therapist,
    TherapistPatient,
    User,
)


@transaction.atomic
def create_organisation_invitation(*, admin, email, dataCaducitat=None):
    membership = admin.organisation_memberships.select_related("organisation").filter(
        is_admin=True,
    ).first()
    if membership is None:
        raise DjangoValidationError(
            {"detail": ["Només un terapeuta administrador pot generar invitacions."]}
        )

    organisation = membership.organisation
    if organisation.type != Organisation.Type.CLINIC:
        raise DjangoValidationError(
            {"detail": ["Les organitzacions individuals no poden generar invitacions."]}
        )

    normalized_email = User.objects.normalize_email(email)
    if User.objects.filter(email__iexact=normalized_email).exists():
        raise DjangoValidationError(
            {"email": ["Ja existeix un usuari amb aquest correu electrònic."]}
        )

    invitation = InvitacioOrganitzacio.objects.create(
        email=normalized_email,
        idOrganitzacio=organisation,
        dataCaducitat=dataCaducitat,
    )
    invitation_url = build_organisation_invitation_url(invitation)
    send_organisation_invitation_email(
        invitation=invitation,
        admin=admin,
        invitation_url=invitation_url,
    )
    return invitation


@transaction.atomic
def register_therapist(
    *,
    first_name,
    last_name,
    email,
    license_number,
    specialty,
    registration_path,
    organisation_name=None,
    invitation_token=None,
):
    invitation = None
    organisation = None
    is_admin = False

    if registration_path == "independent":
        organisation = Organisation.objects.create(
            name=organisation_name or f"{first_name} {last_name}",
            type=Organisation.Type.INDIVIDUAL,
        )
    elif registration_path == "create_clinic":
        organisation = Organisation.objects.create(
            name=organisation_name,
            type=Organisation.Type.CLINIC,
        )
        is_admin = True
    elif registration_path == "join_organisation":
        invitation = (
            InvitacioOrganitzacio.objects.select_for_update()
            .select_related("idOrganitzacio")
            .filter(token=invitation_token)
            .first()
        )
        if invitation is None or not invitation.is_usable:
            raise DjangoValidationError(
                {"invitation_token": ["La invitació no és vàlida, ja s'ha usat o ha caducat."]}
            )
        organisation = invitation.idOrganitzacio
        if organisation.type != Organisation.Type.CLINIC:
            raise DjangoValidationError(
                {"invitation_token": ["La invitació no pertany a una organització clínica."]}
            )
        if invitation.email and invitation.email.lower() != email.lower():
            raise DjangoValidationError(
                {"email": ["Aquest token d'invitació està vinculat a un altre correu electrònic."]}
            )
    else:
        raise DjangoValidationError({"registration_path": ["Camí de registre no vàlid."]})

    therapist = Therapist(
        email=email,
        first_name=first_name,
        last_name=last_name,
        license_number=license_number,
        specialty=specialty,
        role=User.Role.THERAPIST,
        is_active=False,
    )
    therapist.set_unusable_password()
    therapist.save()
    
    OrganisationMember.objects.create(
        user=therapist,
        organisation=organisation,
        is_admin=is_admin,
    )

    if invitation is not None:
        invitation.usat = True
        invitation.save(update_fields=["usat"])
        
    activation_url = build_account_activation_url(therapist)
    send_therapist_activation_email(therapist=therapist, activation_url=activation_url)
    return therapist, activation_url


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
        role=User.Role.PATIENT,
        is_active=False,
    )
    patient.set_unusable_password()
    patient.save()
    TherapistPatient.objects.create(patient=patient, therapist=therapist)
    activation_url = build_account_activation_url(patient)
    send_patient_activation_email(patient=patient, therapist=therapist, activation_url=activation_url)
    return patient, activation_url


def build_account_activation_url(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return f"{settings.FRONTEND_URL.rstrip('/')}/activate-account?uid={uid}&token={token}"


def build_organisation_invitation_url(invitation):
    query_params = {"token": invitation.token}
    if invitation.email:
        query_params["email"] = invitation.email
    query = urlencode(query_params)
    return f"{settings.FRONTEND_URL.rstrip('/')}/register/therapist?{query}"


def send_organisation_invitation_email(*, invitation, admin, invitation_url):
    organisation = invitation.idOrganitzacio
    subject = f"Invitació per unir-te a {organisation.name} a Reflexia"
    message = (
        f"Hola,\n\n"
        f"{admin.first_name} {admin.last_name} t'ha convidat a unir-te a {organisation.name} a Reflexia.\n"
        "Fes servir aquest enllaç per completar el registre com a terapeuta:\n\n"
        f"{invitation_url}\n\n"
        "Aquest enllaç només es pot utilitzar una vegada."
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [invitation.email],
        fail_silently=False,
    )


def send_clinic_admin_activation_email(*, user, organisation, activation_url):
    subject = "Activate your Reflexia clinic admin account"
    message = (
        f"Hello {user.first_name},\n\n"
        f"You have been registered as the administrator for {organisation.name}.\n"
        "Use the following link to set your password and activate your access:\n\n"
        f"{activation_url}\n\n"
        "If you were not expecting this email, you can ignore it."
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def send_therapist_activation_email(*, therapist, activation_url):
    subject = "Activate your Reflexia therapist account"
    message = (
        f"Hello {therapist.first_name},\n\n"
        "An administrator has created your Reflexia therapist account.\n"
        "Use the following link to set your password and activate your access:\n\n"
        f"{activation_url}\n\n"
        "If you were not expecting this email, you can ignore it."
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [therapist.email],
        fail_silently=False,
    )


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


def build_password_reset_url(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?uid={uid}&token={token}"


def send_password_reset_email(*, user, reset_url):
    subject = "Reset your Reflexia password"
    message = (
        f"Hello {user.first_name},\n\n"
        "We received a request to reset your Reflexia password.\n"
        "Use the following link to choose a new password:\n\n"
        f"{reset_url}\n\n"
        "If you did not request this change, you can ignore this email."
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def send_account_deleted_email(*, user_email):
    subject = "Your Reflexia account has been deleted"
    message = (
        "Your Reflexia account has been deactivated successfully.\n\n"
        "Non-clinical profile data has been removed, and clinical records will be retained "
        "only for the legally required period."
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
        fail_silently=False,
    )


@transaction.atomic
def activate_user_account(*, user, password):
    validate_password(password, user=user)
    user.set_password(password)
    user.is_active = True
    user.save(update_fields=["password", "is_active"])
    return user


@transaction.atomic
def reset_user_password(*, user, password):
    validate_password(password, user=user)
    user.set_password(password)
    if not user.is_active:
        user.is_active = True
        user.save(update_fields=["password", "is_active"])
    else:
        user.save(update_fields=["password"])
    return user


@transaction.atomic
def update_user_profile(*, user, email=None, specialty=None):
    update_fields = []

    if email is not None and user.email != email:
        user.email = email
        update_fields.append("email")

    if hasattr(user, "therapist_profile") and specialty is not None:
        therapist = user.therapist_profile
        if therapist.specialty != specialty:
            therapist.specialty = specialty
            therapist.save(update_fields=["specialty"])

    if update_fields:
        user.save(update_fields=update_fields)
    return user


@transaction.atomic
def change_user_password(*, user, current_password, new_password):
    if not user.check_password(current_password):
        raise DjangoValidationError({"current_password": ["Current password is incorrect."]})

    validate_password(new_password, user=user)
    user.set_password(new_password)
    user.save(update_fields=["password"])
    return user


@transaction.atomic
def delete_user_account(*, user):
    if hasattr(user, "therapist_profile"):
        active_patient_links = TherapistPatient.objects.filter(
            therapist=user.therapist_profile,
            patient__is_active=True,
        ).select_related("patient")
        active_patients_count = active_patient_links.count()
        if active_patients_count > 0:
            raise DjangoValidationError(
                {
                    "assigned_patients": [f"This therapist still has {active_patients_count} active patients."],
                    "patients": [
                        {
                            "id": str(link.patient.pk),
                            "first_name": link.patient.first_name,
                            "last_name": link.patient.last_name,
                            "email": link.patient.email,
                        }
                        for link in active_patient_links
                    ],
                }
            )

    # Check if user is the sole admin of any organisation
    sole_admin_orgs = []
    memberships = user.organisation_memberships.filter(is_admin=True)
    for membership in memberships:
        admin_count = OrganisationMember.objects.filter(
            organisation=membership.organisation,
            is_admin=True
        ).count()
        if admin_count <= 1:
            # We only block if there are other members who need an admin.
            # If they are the ONLY member, the organisation will effectively be empty/inactive.
            # However, the user request says "if it is only one user, this will be the admin".
            # This implies even if they are alone, they are admin. If they delete themselves, 
            # the org is empty. That's usually acceptable if the whole account is being deleted, 
            # but to be safe and follow the spirit of "always have an admin", we block it 
            # if they are managing a clinic with other therapists.
            member_count = OrganisationMember.objects.filter(organisation=membership.organisation).count()
            if member_count > 1:
                sole_admin_orgs.append(membership.organisation)

    if sole_admin_orgs:
        raise DjangoValidationError(
            {
                "sole_admin_organisations": [
                    f"Ets l'únic administrador de {len(sole_admin_orgs)} organitzacions."
                ],
                "organisations": [
                    {
                        "id": str(org.pk),
                        "name": org.name,
                    }
                    for org in sole_admin_orgs
                ],
            }
        )

    original_email = user.email
    anonymized_identifier = str(user.pk)
    user.email = f"deleted-{anonymized_identifier}@deleted.reflexia.local"
    user.first_name = "Deleted"
    user.last_name = "User"
    user.two_factor_enabled = False
    user.two_factor_secret = ""
    user.two_factor_pending_secret = ""
    user.is_active = False
    user.set_unusable_password()
    user.save(
        update_fields=[
            "email",
            "first_name",
            "last_name",
            "two_factor_enabled",
            "two_factor_secret",
            "two_factor_pending_secret",
            "is_active",
            "password",
        ]
    )
    send_account_deleted_email(user_email=original_email)
    return user


@transaction.atomic
def deactivate_patient_by_therapist(*, therapist, patient):
    relation_exists = TherapistPatient.objects.filter(
        therapist=therapist,
        patient=patient,
    ).exists()
    if not relation_exists:
        raise DjangoValidationError({"patient": ["This patient is not assigned to the authenticated therapist."]})

    patient.email = f"deleted-{patient.pk}@deleted.reflexia.local"
    patient.first_name = "Deleted"
    patient.last_name = "Patient"
    patient.two_factor_enabled = False
    patient.two_factor_secret = ""
    patient.two_factor_pending_secret = ""
    patient.is_active = False
    patient.set_unusable_password()
    patient.save(
        update_fields=[
            "email",
            "first_name",
            "last_name",
            "two_factor_enabled",
            "two_factor_secret",
            "two_factor_pending_secret",
            "is_active",
            "password",
        ]
    )
    return patient
