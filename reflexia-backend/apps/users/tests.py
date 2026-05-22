from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
import pyotp
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import (
    InvitacioOrganitzacio,
    Organisation,
    Patient,
    ProfessionalDirectoryEntry,
    Therapist,
    TherapistPatient,
    User,
    OrganisationMember,
)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_URL="http://localhost:5173",
)
class TherapistRegistrationTests(APITestCase):
    def setUp(self):
        ProfessionalDirectoryEntry.objects.create(
            license_number="30809",
            complete_name="LAURA GOMEZ",
        )
        ProfessionalDirectoryEntry.objects.create(
            license_number="21039",
            complete_name="MARTA LOPEZ",
        )
        ProfessionalDirectoryEntry.objects.create(
            license_number="17105",
            complete_name="JOAN SERRA",
        )
        self.url = "/api/users/register/therapist/"

    def test_register_independent_therapist_creates_individual_organisation(self):
        payload = {
            "first_name": "Laura",
            "last_name": "Gomez",
            "email": "laura@example.com",
            "license_number": "30809",
            "specialty": "Clinical Psychology",
            "registration_path": "independent",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Therapist.objects.count(), 1)
        self.assertEqual(Organisation.objects.count(), 1)
        therapist = Therapist.objects.get(email="laura@example.com")
        organisation = therapist.organisation
        self.assertEqual(therapist.first_name, "Laura")
        self.assertEqual(therapist.license_number, "30809")
        self.assertEqual(organisation.type, Organisation.Type.INDIVIDUAL)
        self.assertEqual(OrganisationMember.objects.get(user=therapist).is_admin, False)
        self.assertFalse(therapist.is_active)
        self.assertFalse(therapist.has_usable_password())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("activate-account", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, ["laura@example.com"])
        self.assertNotIn("password", response.data)

    def test_register_therapist_can_create_clinic_as_admin(self):
        payload = {
            "first_name": "Marta",
            "last_name": "Lopez",
            "email": "marta@example.com",
            "license_number": "21039",
            "specialty": "Clinical Psychology",
            "registration_path": "create_clinic",
            "organisation_name": "Centre Reflexia",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        therapist = Therapist.objects.get(email="marta@example.com")
        organisation = therapist.organisation
        self.assertEqual(organisation.name, "Centre Reflexia")
        self.assertEqual(organisation.type, Organisation.Type.CLINIC)
        self.assertTrue(
            OrganisationMember.objects.filter(
                user=therapist,
                organisation=organisation,
                is_admin=True,
            ).exists()
        )
        self.assertTrue(response.data["is_clinic_admin"])

    def test_register_therapist_can_join_existing_organisation_with_invitation(self):
        admin = Therapist.objects.create_user(
            email="admin-clinic@example.com",
            password="StrongPass123!",
            first_name="Admin",
            last_name="Clinic",
            license_number="21039",
            specialty="Clinical Psychology",
        )
        org = Organisation.objects.create(name="Test Clinic", type=Organisation.Type.CLINIC)
        OrganisationMember.objects.create(user=admin, organisation=org, is_admin=True)
        invitation = InvitacioOrganitzacio.objects.create(idOrganitzacio=org)
        payload = {
            "first_name": "Joan",
            "last_name": "Serra",
            "email": "joan@example.com",
            "license_number": "17105",
            "specialty": "Trauma Therapy",
            "registration_path": "join_organisation",
            "invitation_token": invitation.token,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        therapist = Therapist.objects.get(email="joan@example.com")
        self.assertTrue(
            OrganisationMember.objects.filter(
                user=therapist,
                organisation=org,
                is_admin=False,
            ).exists()
        )
        invitation.refresh_from_db()
        self.assertTrue(invitation.usat)

    def test_register_therapist_rejects_used_invitation(self):
        org = Organisation.objects.create(name="Test Clinic", type=Organisation.Type.CLINIC)
        invitation = InvitacioOrganitzacio.objects.create(idOrganitzacio=org, usat=True)

        response = self.client.post(
            self.url,
            {
                "first_name": "Laura",
                "last_name": "Gomez",
                "email": "laura@example.com",
                "license_number": "30809",
                "specialty": "Clinical Psychology",
                "registration_path": "join_organisation",
                "invitation_token": invitation.token,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("invitation_token", response.data)
        self.assertEqual(Therapist.objects.count(), 0)

    def test_register_therapist_rejects_invitation_email_mismatch(self):
        org = Organisation.objects.create(name="Test Clinic", type=Organisation.Type.CLINIC)
        invitation = InvitacioOrganitzacio.objects.create(
            idOrganitzacio=org,
            email="joan@example.com",
        )

        response = self.client.post(
            self.url,
            {
                "first_name": "Laura",
                "last_name": "Gomez",
                "email": "laura@example.com",
                "license_number": "30809",
                "specialty": "Clinical Psychology",
                "registration_path": "join_organisation",
                "invitation_token": invitation.token,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(Therapist.objects.count(), 0)

    def test_register_therapist_rejects_unknown_license_number(self):
        payload = {
            "first_name": "Laura",
            "last_name": "Gomez",
            "email": "laura@example.com",
            "license_number": "99999",
            "specialty": "Clinical Psychology",
            "registration_path": "independent",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("license_number", response.data)
        self.assertEqual(Therapist.objects.count(), 0)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_URL="http://localhost:5173",
)
class OrganisationInvitationTests(APITestCase):
    def setUp(self):
        self.url = "/api/users/admin/organisations/invitations/"
        self.clinic = Organisation.objects.create(
            name="Test Clinic",
            type=Organisation.Type.CLINIC,
        )
        self.individual = Organisation.objects.create(
            name="Independent",
            type=Organisation.Type.INDIVIDUAL,
        )
        self.admin = Therapist.objects.create_user(
            email="clinic-admin@example.com",
            password="StrongPass123!",
            first_name="Marta",
            last_name="Lopez",
            license_number="16385",
            specialty="Clinical Psychology",
            is_active=True,
        )
        OrganisationMember.objects.create(user=self.admin, organisation=self.clinic, is_admin=True)
        self.member = Therapist.objects.create_user(
            email="member@example.com",
            password="StrongPass123!",
            first_name="Joan",
            last_name="Serra",
            license_number="17105",
            specialty="Clinical Psychology",
            is_active=True,
        )
        OrganisationMember.objects.create(user=self.member, organisation=self.clinic, is_admin=False)
        self.independent_therapist = Therapist.objects.create_user(
            email="solo@example.com",
            password="StrongPass123!",
            first_name="Solo",
            last_name="Therapist",
            license_number="21039",
            specialty="Clinical Psychology",
            is_active=True,
        )
        OrganisationMember.objects.create(
            user=self.independent_therapist,
            organisation=self.individual,
            is_admin=False,
        )

    def test_clinic_admin_can_create_invitation_for_their_organisation(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            self.url,
            {"email": "new-therapist@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        invitation = InvitacioOrganitzacio.objects.get(token=response.data["token"])
        self.assertEqual(invitation.idOrganitzacio, self.clinic)
        self.assertEqual(invitation.email, "new-therapist@example.com")
        self.assertFalse(invitation.usat)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["new-therapist@example.com"])
        self.assertIn("/register/therapist?", mail.outbox[0].body)
        self.assertIn(f"token={invitation.token}", mail.outbox[0].body)
        self.assertIn("email=new-therapist%40example.com", mail.outbox[0].body)

    def test_clinic_admin_cannot_invite_existing_user_email(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            self.url,
            {"email": self.member.email},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(InvitacioOrganitzacio.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_non_admin_cannot_create_invitation(self):
        self.client.force_authenticate(user=self.member)

        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(InvitacioOrganitzacio.objects.count(), 0)

    def test_individual_organisation_cannot_create_invitation(self):
        self.client.force_authenticate(user=self.independent_therapist)

        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(InvitacioOrganitzacio.objects.count(), 0)


class OrganisationMembershipConstraintTests(APITestCase):
    def setUp(self):
        self.individual = Organisation.objects.create(
            name="Individual",
            type=Organisation.Type.INDIVIDUAL,
        )
        self.clinic = Organisation.objects.create(
            name="Clinic",
            type=Organisation.Type.CLINIC,
        )
        self.therapist = Therapist.objects.create_user(
            email="therapist-constraint@example.com",
            password="StrongPass123!",
            first_name="Marta",
            last_name="Lopez",
            license_number="16385",
            specialty="Clinical Psychology",
            legal_terms_accepted=True,
        )
        self.other_therapist = Therapist.objects.create_user(
            email="other-constraint@example.com",
            password="StrongPass123!",
            first_name="Joan",
            last_name="Serra",
            license_number="17105",
            specialty="Clinical Psychology",
        )

    def test_individual_organisation_accepts_only_one_member(self):
        OrganisationMember.objects.create(
            user=self.therapist,
            organisation=self.individual,
            is_admin=False,
        )

        with self.assertRaises(ValidationError):
            OrganisationMember.objects.create(
                user=self.other_therapist,
                organisation=self.individual,
                is_admin=False,
            )

    def test_therapist_can_only_belong_to_one_organisation(self):
        OrganisationMember.objects.create(
            user=self.therapist,
            organisation=self.individual,
            is_admin=False,
        )

        with self.assertRaises(ValidationError):
            OrganisationMember.objects.create(
                user=self.therapist,
                organisation=self.clinic,
                is_admin=False,
            )


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_URL="http://localhost:5173",
)
class PatientRegistrationTests(APITestCase):
    def setUp(self):
        self.org = Organisation.objects.create(
            name="Test Clinic",
            type=Organisation.Type.CLINIC,
        )
        self.therapist = Therapist.objects.create_user(
            email="therapist@example.com",
            password="StrongPass123!",
            first_name="Marta",
            last_name="Lopez",
            license_number="16385",
            specialty="Clinical Psychology",
            legal_terms_accepted=True,
        )
        OrganisationMember.objects.create(user=self.therapist, organisation=self.org, is_admin=True)
        self.url = "/api/users/register/patient/"

    def test_register_patient_successfully_for_therapist(self):
        self.client.force_authenticate(user=self.therapist)
        payload = {
            "first_name": "Pablo",
            "last_name": "Martin",
            "email": "pablo@example.com",
            "birth_date": "2000-05-10",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Patient.objects.count(), 1)
        self.assertEqual(TherapistPatient.objects.count(), 1)
        patient = Patient.objects.get(email="pablo@example.com")
        relation = TherapistPatient.objects.get(patient=patient)
        self.assertEqual(relation.therapist, self.therapist)
        self.assertFalse(patient.is_active)
        self.assertFalse(patient.has_usable_password())
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(response.data["activation_email_sent"])
        self.assertIn("activate-account", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, ["pablo@example.com"])

    def test_register_patient_requires_therapist_user(self):
        response = self.client.post(
            self.url,
            {
                "first_name": "Pablo",
                "last_name": "Martin",
                "email": "pablo@example.com",
                "birth_date": "2000-05-10",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Patient.objects.count(), 0)

    def test_register_patient_rejects_duplicate_email(self):
        self.client.force_authenticate(user=self.therapist)
        User.objects.create_user(
            email="pablo@example.com",
            password="AnotherPass123!",
            first_name="Existing",
            last_name="User",
        )

        response = self.client.post(
            self.url,
            {
                "first_name": "Pablo",
                "last_name": "Martin",
                "email": "pablo@example.com",
                "birth_date": "2000-05-10",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TherapistPatientManagementTests(APITestCase):
    def setUp(self):
        self.org = Organisation.objects.create(
            name="Test Clinic",
            type=Organisation.Type.CLINIC,
        )
        self.therapist = Therapist.objects.create_user(
            email="therapist@example.com",
            password="StrongPass123!",
            first_name="Marta",
            last_name="Lopez",
            license_number="16385",
            specialty="Clinical Psychology",
            is_active=True,
        )
        OrganisationMember.objects.create(user=self.therapist, organisation=self.org, is_admin=True)

        self.patient = Patient.objects.create_user(
            email="patient@example.com",
            password="StrongPass123!",
            first_name="Paula",
            last_name="Sanchez",
            birth_date="2001-01-10",
            is_active=True,
        )
        self.other_patient = Patient.objects.create_user(
            email="other@example.com",
            password="StrongPass123!",
            first_name="Joan",
            last_name="Serra",
            birth_date="2000-03-15",
            is_active=True,
        )
        # Link patients to therapist (required for therapist patience list)
        TherapistPatient.objects.create(therapist=self.therapist, patient=self.patient)
        self.list_url = "/api/users/patients/"
        self.register_url = "/api/users/register/patient/"

    def test_therapist_can_list_assigned_patients(self):
        self.client.force_authenticate(user=self.therapist)

        response = self.client.get(self.list_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(self.patient.pk))
        self.assertEqual(response.data[0]["email"], self.patient.email)
        self.assertIn("email", response.data[0])
        self.assertEqual(Patient.objects.count(), 2)

    def test_registered_patient_starts_with_pending_legal_acceptance(self):
        self.client.force_authenticate(user=self.therapist)
        response = self.client.post(
            self.register_url,
            {
                "first_name": "Pablo",
                "last_name": "Martin",
                "email": "pablo@example.com",
                "birth_date": "2000-05-10",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        patient = Patient.objects.get(email="pablo@example.com")
        self.assertFalse(patient.legal_terms_accepted)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AccountActivationTests(APITestCase):
    def setUp(self):
        self.patient = Patient.objects.create(
            email="patient@example.com",
            first_name="Paula",
            last_name="Sanchez",
            birth_date="2001-01-10",
            is_active=False,
        )
        self.patient.set_unusable_password()
        self.patient.save(update_fields=["password", "is_active"])
        self.therapist = Therapist.objects.create(
            email="therapist@example.com",
            first_name="Marta",
            last_name="Lopez",
            license_number="16385",
            specialty="Clinical Psychology",
            is_active=False,
        )
        self.therapist.set_unusable_password()
        self.therapist.save(update_fields=["password", "is_active"])
        self.url = "/api/users/activate/account/"

    def test_activate_patient_account_successfully(self):
        uid = urlsafe_base64_encode(force_bytes(self.patient.pk))
        token = default_token_generator.make_token(self.patient)

        response = self.client.post(
            self.url,
            {
                "uid": uid,
                "token": token,
                "password": "StrongPass123!",
                "password_confirm": "StrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.patient.refresh_from_db()
        self.assertTrue(self.patient.is_active)
        self.assertTrue(self.patient.check_password("StrongPass123!"))

    def test_activate_therapist_account_successfully(self):
        uid = urlsafe_base64_encode(force_bytes(self.therapist.pk))
        token = default_token_generator.make_token(self.therapist)

        response = self.client.post(
            self.url,
            {
                "uid": uid,
                "token": token,
                "password": "StrongPass123!",
                "password_confirm": "StrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.therapist.refresh_from_db()
        self.assertTrue(self.therapist.is_active)
        self.assertTrue(self.therapist.check_password("StrongPass123!"))

    def test_activate_patient_account_rejects_invalid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.patient.pk))

        response = self.client.post(
            self.url,
            {
                "uid": uid,
                "token": "invalid-token",
                "password": "StrongPass123!",
                "password_confirm": "StrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.patient.refresh_from_db()
        self.assertFalse(self.patient.is_active)


class LoginTests(APITestCase):
    def setUp(self):
        self.org = Organisation.objects.create(
            name="Test Clinic",
            type=Organisation.Type.CLINIC,
        )
        self.therapist = Therapist.objects.create_user(
            email="therapist@example.com",
            password="StrongPass123!",
            first_name="Marta",
            last_name="Lopez",
            license_number="16385",
            specialty="Clinical Psychology",
            legal_terms_accepted=True,
        )
        OrganisationMember.objects.create(user=self.therapist, organisation=self.org, is_admin=True)

        self.patient = Patient.objects.create_user(
            email="patient@example.com",
            password="StrongPass123!",
            first_name="Paula",
            last_name="Sanchez",
            birth_date="2001-01-10",
            is_active=True,
        )
        self.inactive_patient = Patient.objects.create(
            email="inactive@example.com",
            first_name="Inactive",
            last_name="Patient",
            birth_date="2002-02-02",
            role=User.Role.PATIENT,
            is_active=False,
        )
        self.inactive_patient.set_password("StrongPass123!")
        self.inactive_patient.save(update_fields=["password", "is_active"])
        self.login_url = "/api/users/login/"
        self.logout_url = "/api/users/logout/"
        self.me_url = "/api/users/me/"
        self.accept_consent_url = "/api/users/consent/accept/"
        self.reject_consent_url = "/api/users/consent/reject/"
        self.two_factor_setup_url = "/api/users/2fa/setup/"
        self.two_factor_enable_url = "/api/users/2fa/enable/"
        self.two_factor_verify_url = "/api/users/2fa/verify/"
        self.two_factor_disable_url = "/api/users/2fa/disable/"

    def test_login_returns_jwt_tokens_for_therapist(self):
        response = self.client.post(
            self.login_url,
            {"email": "therapist@example.com", "password": "StrongPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["login_status"], "authenticated")
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["role"], "therapist")

    def test_login_returns_jwt_tokens_for_patient_with_consent(self):
        self.patient.legal_terms_accepted = True
        self.patient.save(update_fields=["legal_terms_accepted"])

        response = self.client.post(
            self.login_url,
            {"email": "patient@example.com", "password": "StrongPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["login_status"], "authenticated")
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["role"], "patient")

    def test_login_requires_legal_acceptance_before_home(self):
        self.patient.legal_terms_accepted = False
        self.patient.save(update_fields=["legal_terms_accepted"])

        response = self.client.post(
            self.login_url,
            {"email": "patient@example.com", "password": "StrongPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["login_status"], "consent_required")
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_requires_therapist_legal_acceptance_before_home(self):
        self.therapist.legal_terms_accepted = False
        self.therapist.save(update_fields=["legal_terms_accepted"])

        response = self.client.post(
            self.login_url,
            {"email": "therapist@example.com", "password": "StrongPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["login_status"], "consent_required")

    def test_login_flags_two_factor_when_enabled(self):
        self.therapist.two_factor_enabled = True
        self.therapist.save(update_fields=["two_factor_enabled"])

        response = self.client.post(
            self.login_url,
            {"email": "therapist@example.com", "password": "StrongPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["login_status"], "two_factor_required")
        self.assertIsNone(response.data["access"])
        self.assertIsNone(response.data["refresh"])

    def test_login_rejects_inactive_patient(self):
        response = self.client.post(
            self.login_url,
            {"email": "inactive@example.com", "password": "StrongPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data["detail"][0]), "This account is inactive. Please activate it first.")

    def test_login_rejects_invalid_credentials(self):
        response = self.client.post(
            self.login_url,
            {"email": "therapist@example.com", "password": "wrong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data["detail"][0]), "Invalid email or password.")

    def test_me_returns_authenticated_user(self):
        refresh = RefreshToken.for_user(self.therapist)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "therapist@example.com")
        self.assertEqual(response.data["role"], "therapist")

    def test_logout_blacklists_refresh_token(self):
        refresh = RefreshToken.for_user(self.therapist)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = self.client.post(self.logout_url, {"refresh": str(refresh)}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        outstanding_token = OutstandingToken.objects.get(user=self.therapist)
        self.assertTrue(BlacklistedToken.objects.filter(token=outstanding_token).exists())

    def test_user_can_accept_consent(self):
        refresh = RefreshToken.for_user(self.patient)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = self.client.post(self.accept_consent_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.patient.refresh_from_db()
        self.assertTrue(self.patient.legal_terms_accepted)
        self.assertIsNotNone(self.patient.legal_terms_accepted_at)
        self.assertEqual(self.patient.legal_terms_version, User.LEGAL_TERMS_VERSION)

    def test_user_can_reject_consent_and_account_becomes_inactive(self):
        refresh = RefreshToken.for_user(self.patient)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = self.client.post(
            self.reject_consent_url,
            {"refresh": str(refresh)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.patient.refresh_from_db()
        self.assertFalse(self.patient.legal_terms_accepted)
        self.assertFalse(self.patient.is_active)
        outstanding_token = OutstandingToken.objects.get(user=self.patient)
        self.assertTrue(BlacklistedToken.objects.filter(token=outstanding_token).exists())

    def test_user_can_setup_and_enable_two_factor(self):
        refresh = RefreshToken.for_user(self.therapist)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        setup_response = self.client.post(self.two_factor_setup_url, format="json")

        self.assertEqual(setup_response.status_code, status.HTTP_200_OK)
        self.assertIn("secret", setup_response.data)
        self.assertIn("otpauth_url", setup_response.data)

        code = pyotp.TOTP(setup_response.data["secret"]).now()
        enable_response = self.client.post(
            self.two_factor_enable_url,
            {"code": code},
            format="json",
        )

        self.assertEqual(enable_response.status_code, status.HTTP_200_OK)
        self.therapist.refresh_from_db()
        self.assertTrue(self.therapist.two_factor_enabled)
        self.assertTrue(self.therapist.two_factor_secret)

    def test_login_with_two_factor_can_be_completed(self):
        secret = pyotp.random_base32()
        self.therapist.two_factor_enabled = True
        self.therapist.two_factor_secret = secret
        self.therapist.save(update_fields=["two_factor_enabled", "two_factor_secret"])

        login_response = self.client.post(
            self.login_url,
            {"email": "therapist@example.com", "password": "StrongPass123!"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertEqual(login_response.data["login_status"], "two_factor_required")

        verify_response = self.client.post(
            self.two_factor_verify_url,
            {
                "email": "therapist@example.com",
                "password": "StrongPass123!",
                "code": pyotp.TOTP(secret).now(),
            },
            format="json",
        )

        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.assertEqual(verify_response.data["login_status"], "authenticated")
        self.assertIn("access", verify_response.data)
        self.assertIn("refresh", verify_response.data)

    def test_user_can_disable_two_factor(self):
        secret = pyotp.random_base32()
        self.therapist.two_factor_enabled = True
        self.therapist.two_factor_secret = secret
        self.therapist.save(update_fields=["two_factor_enabled", "two_factor_secret"])

        refresh = RefreshToken.for_user(self.therapist)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = self.client.post(
            self.two_factor_disable_url,
            {
                "password": "StrongPass123!",
                "code": pyotp.TOTP(secret).now(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.therapist.refresh_from_db()
        self.assertFalse(self.therapist.two_factor_enabled)
        self.assertEqual(self.therapist.two_factor_secret, "")


class ConsentDocumentTests(APITestCase):
    def test_consent_document_is_available(self):
        response = self.client.get("/api/users/consent/document/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_professional_consent_document_is_available(self):
        response = self.client.get("/api/users/consent/document/?role=therapist")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_URL="http://localhost:5173",
)
class PasswordRecoveryTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="recover@example.com",
            password="StrongPass123!",
            first_name="Recover",
            last_name="User",
        )
        self.forgot_url = "/api/users/password/forgot/"
        self.reset_url = "/api/users/password/reset/"

    def test_forgot_password_sends_email_when_user_exists(self):
        response = self.client.post(
            self.forgot_url,
            {"email": "recover@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("reset-password", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, ["recover@example.com"])

    def test_forgot_password_returns_same_response_for_unknown_email(self):
        response = self.client.post(
            self.forgot_url,
            {"email": "unknown@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_reset_password_updates_user_password(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        response = self.client.post(
            self.reset_url,
            {
                "uid": uid,
                "token": token,
                "password": "NewStrongPass123!",
                "password_confirm": "NewStrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPass123!"))

    def test_reset_password_rejects_invalid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        response = self.client.post(
            self.reset_url,
            {
                "uid": uid,
                "token": "invalid-token",
                "password": "NewStrongPass123!",
                "password_confirm": "NewStrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class ProfileManagementTests(APITestCase):
    def setUp(self):
        self.org = Organisation.objects.create(
            name="Test Clinic",
            type=Organisation.Type.CLINIC,
        )
        self.patient = Patient.objects.create_user(
            email="patient-profile@example.com",
            password="StrongPass123!",
            first_name="Paula",
            last_name="Sanchez",
            birth_date="2001-01-10",
            is_active=True,
        )
        self.therapist = Therapist.objects.create_user(
            email="therapist-profile@example.com",
            password="StrongPass123!",
            first_name="Marta",
            last_name="Lopez",
            license_number="21039",
            specialty="Clinical Psychology",
        )
        OrganisationMember.objects.create(user=self.therapist, organisation=self.org, is_admin=True)
        self.patient_me_url = "/api/users/me/"
        self.change_password_url = "/api/users/change-password/"
        self.delete_account_url = "/api/users/delete-account/"
        self.patient_deactivate_url = "/api/users/patients/deactivate/"

    def test_patient_can_update_email(self):
        refresh = RefreshToken.for_user(self.patient)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = self.client.patch(
            self.patient_me_url,
            {"email": "new-patient@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.email, "new-patient@example.com")

    def test_therapist_can_update_email_and_specialty(self):
        refresh = RefreshToken.for_user(self.therapist)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = self.client.patch(
            self.patient_me_url,
            {
                "email": "new-therapist@example.com",
                "specialty": "Trauma Therapy",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.therapist.refresh_from_db()
        self.assertEqual(self.therapist.email, "new-therapist@example.com")
        self.assertEqual(self.therapist.specialty, "Trauma Therapy")

    def test_patient_cannot_update_specialty(self):
        refresh = RefreshToken.for_user(self.patient)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = self.client.patch(
            self.patient_me_url,
            {"specialty": "Not Allowed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("specialty", response.data)

    def test_user_can_change_password(self):
        refresh = RefreshToken.for_user(self.patient)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = self.client.post(
            self.change_password_url,
            {
                "current_password": "StrongPass123!",
                "new_password": "NewStrongPass123!",
                "new_password_confirm": "NewStrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.patient.refresh_from_db()
        self.assertTrue(self.patient.check_password("NewStrongPass123!"))

    def test_patient_can_delete_own_account(self):
        refresh = RefreshToken.for_user(self.patient)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = self.client.post(
            self.delete_account_url,
            {
                "password": "StrongPass123!",
                "refresh": str(refresh),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.patient.refresh_from_db()
        self.assertFalse(self.patient.is_active)
        self.assertTrue(self.patient.email.startswith("deleted-"))
        self.assertEqual(len(mail.outbox), 1)

    def test_therapist_cannot_delete_account_with_assigned_patients(self):
        assigned_patient = Patient.objects.create_user(
            email="assigned@example.com",
            password="StrongPass123!",
            first_name="Assigned",
            last_name="Patient",
            birth_date="2000-01-01",
            is_active=True,
        )
        TherapistPatient.objects.create(patient=assigned_patient, therapist=self.therapist)

        refresh = RefreshToken.for_user(self.therapist)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = self.client.post(
            self.delete_account_url,
            {
                "password": "StrongPass123!",
                "refresh": str(refresh),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("assigned_patients", response.data)
        self.assertIn("patients", response.data)
        self.assertIn("assigned@example.com", str(response.data["patients"]))

    def test_therapist_can_deactivate_patient_from_delete_flow(self):
        assigned_patient = Patient.objects.create_user(
            email="assigned@example.com",
            password="StrongPass123!",
            first_name="Assigned",
            last_name="Patient",
            birth_date="2000-01-01",
            is_active=True,
        )
        TherapistPatient.objects.create(patient=assigned_patient, therapist=self.therapist)

        refresh = RefreshToken.for_user(self.therapist)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = self.client.post(
            self.patient_deactivate_url,
            {"patient_id": str(assigned_patient.pk)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assigned_patient.refresh_from_db()
        self.assertFalse(assigned_patient.is_active)
        self.assertTrue(assigned_patient.email.startswith("deleted-"))

    def test_therapist_can_delete_account_after_deactivating_assigned_patients(self):
        assigned_patient = Patient.objects.create_user(
            email="assigned@example.com",
            password="StrongPass123!",
            first_name="Assigned",
            last_name="Patient",
            birth_date="2000-01-01",
            is_active=True,
        )
        TherapistPatient.objects.create(patient=assigned_patient, therapist=self.therapist)

        therapist_refresh = RefreshToken.for_user(self.therapist)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {therapist_refresh.access_token}")

        deactivate_response = self.client.post(
            self.patient_deactivate_url,
            {"patient_id": str(assigned_patient.pk)},
            format="json",
        )

        self.assertEqual(deactivate_response.status_code, status.HTTP_200_OK)

        delete_response = self.client.post(
            self.delete_account_url,
            {
                "password": "StrongPass123!",
                "refresh": str(therapist_refresh),
            },
            format="json",
        )

        self.assertEqual(delete_response.status_code, status.HTTP_200_OK)
        self.therapist.refresh_from_db()
        self.assertFalse(self.therapist.is_active)
        self.assertTrue(self.therapist.email.startswith("deleted-"))


class MultiTenancyAndAdminTests(APITestCase):
    def setUp(self):
        self.org = Organisation.objects.create(
            name="Test Clinic",
            type=Organisation.Type.CLINIC,
        )
        self.therapist = Therapist.objects.create_user(
            email="therapist@example.com",
            password="StrongPass123!",
            first_name="Marta",
            last_name="Lopez",
            license_number="16385",
            specialty="Clinical Psychology",
            is_active=True,
        )
        OrganisationMember.objects.create(
            user=self.therapist, organisation=self.org, is_admin=True
        )
        self.stats_clinic_url = "/api/users/admin/stats/clinic/"

    def test_clinic_admin_can_get_clinic_stats(self):
        active_patient = Patient.objects.create_user(
            email="active@example.com",
            password="StrongPass123!",
            first_name="Active",
            last_name="Patient",
            birth_date="2000-01-01",
            is_active=True,
        )
        inactive_patient = Patient.objects.create_user(
            email="inactive@example.com",
            password="StrongPass123!",
            first_name="Inactive",
            last_name="Patient",
            birth_date="2000-01-02",
            is_active=False,
        )
        outsider = Patient.objects.create_user(
            email="outsider@example.com",
            password="StrongPass123!",
            first_name="Outside",
            last_name="Patient",
            birth_date="2000-01-03",
            is_active=True,
        )
        TherapistPatient.objects.create(therapist=self.therapist, patient=active_patient)
        TherapistPatient.objects.create(therapist=self.therapist, patient=inactive_patient)

        external_therapist = Therapist.objects.create_user(
            email="external@example.com",
            password="StrongPass123!",
            first_name="External",
            last_name="Therapist",
            license_number="26385",
            specialty="Neuropsychology",
            is_active=True,
        )
        other_org = Organisation.objects.create(
            name="Other Clinic",
            type=Organisation.Type.CLINIC,
        )
        OrganisationMember.objects.create(
            user=external_therapist, organisation=other_org, is_admin=False
        )
        TherapistPatient.objects.create(therapist=external_therapist, patient=outsider)

        self.client.force_authenticate(user=self.therapist)

        response = self.client.get(self.stats_clinic_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_therapists"], 1)
        self.assertEqual(response.data["total_patients"], 1)

    def test_clinic_admin_can_assign_existing_therapist_as_clinic_admin(self):
        self.client.force_authenticate(user=self.therapist)
        therapist_to_assign = Therapist.objects.create_user(
            email="clinic-admin@example.com",
            password="StrongPass123!",
            first_name="Abigail",
            last_name="Sisquella",
            license_number="17105",
            specialty="Psicologia Clínica",
            is_active=True,
        )
        OrganisationMember.objects.create(
            user=therapist_to_assign,
            organisation=self.org,
            is_admin=False,
        )

        response = self.client.patch(
            f"/api/users/admin/therapists/{therapist_to_assign.id}/",
            {"is_admin": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        therapist_to_assign.refresh_from_db()
        self.assertEqual(therapist_to_assign.license_number, "17105")
        self.assertEqual(therapist_to_assign.specialty, "Psicologia Clínica")
        self.assertTrue(
            OrganisationMember.objects.filter(
                user=therapist_to_assign,
                organisation=self.org,
                is_admin=True,
            ).exists()
        )
        self.assertEqual(response.data["license_number"], "17105")
        self.assertEqual(response.data["specialty"], "Psicologia Clínica")
        self.assertTrue(response.data["is_clinic_admin"])

    def test_therapist_cannot_have_multiple_organisations(self):
        second_org = Organisation.objects.create(
            name="Second Clinic",
            type=Organisation.Type.CLINIC,
        )

        with self.assertRaises(ValidationError):
            OrganisationMember.objects.create(
                user=self.therapist,
                organisation=second_org,
                is_admin=False,
            )


class AccessControlTests(APITestCase):
    def setUp(self):
        self.org = Organisation.objects.create(
            name="Test Clinic",
            type=Organisation.Type.CLINIC,
        )
        self.patient = Patient.objects.create_user(
            email="patient@example.com",
            password="StrongPass123!",
            first_name="Paula",
            last_name="Sanchez",
            birth_date="2001-01-10",
            is_active=True,
        )
        self.therapist = Therapist.objects.create_user(
            email="therapist@example.com",
            password="StrongPass123!",
            first_name="Marta",
            last_name="Lopez",
            license_number="16385",
            specialty="Clinical Psychology",
            is_active=True,
        )
        OrganisationMember.objects.create(
            user=self.therapist, organisation=self.org, is_admin=True
        )

    def test_patient_cannot_access_patient_list(self):
        self.client.force_authenticate(user=self.patient)

        response = self.client.get("/api/users/patients/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_access_me(self):
        response = self.client.get("/api/users/me/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patient_cannot_call_patient_deactivate_endpoint(self):
        self.client.force_authenticate(user=self.patient)

        response = self.client.post(
            "/api/users/patients/deactivate/",
            {"patient_id": str(self.patient.pk)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_therapist_can_get_assigned_patient_detail(self):
        TherapistPatient.objects.create(therapist=self.therapist, patient=self.patient)
        self.client.force_authenticate(user=self.therapist)

        response = self.client.get(f"/api/users/patients/{self.patient.pk}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.patient.email)

    def test_therapist_cannot_get_unassigned_patient_detail(self):
        self.client.force_authenticate(user=self.therapist)

        response = self.client.get(f"/api/users/patients/{self.patient.pk}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AdminEntityManagementTests(APITestCase):
    def setUp(self):
        self.org = Organisation.objects.create(
            name="Central Clinic",
            type=Organisation.Type.CLINIC,
        )
        self.other_org = Organisation.objects.create(
            name="Other Clinic",
            type=Organisation.Type.CLINIC,
        )
        self.clinic_admin = Therapist.objects.create_user(
            email="clinic-admin@example.com",
            password="StrongPass123!",
            first_name="Clara",
            last_name="Admin",
            license_number="10001",
            specialty="Clinical Psychology",
            is_active=True,
        )
        self.second_admin = Therapist.objects.create_user(
            email="second-admin@example.com",
            password="StrongPass123!",
            first_name="Joan",
            last_name="Admin",
            license_number="10002",
            specialty="Clinical Psychology",
            is_active=True,
        )
        self.therapist = Therapist.objects.create_user(
            email="therapist-team@example.com",
            password="StrongPass123!",
            first_name="Marta",
            last_name="Lopez",
            license_number="10003",
            specialty="Clinical Psychology",
            is_active=True,
        )
        self.other_therapist = Therapist.objects.create_user(
            email="therapist-other@example.com",
            password="StrongPass123!",
            first_name="Laura",
            last_name="Gomez",
            license_number="10004",
            specialty="Clinical Psychology",
            is_active=True,
        )
        OrganisationMember.objects.create(user=self.clinic_admin, organisation=self.org, is_admin=True)
        OrganisationMember.objects.create(user=self.second_admin, organisation=self.org, is_admin=True)
        OrganisationMember.objects.create(user=self.therapist, organisation=self.org, is_admin=False)
        OrganisationMember.objects.create(user=self.other_therapist, organisation=self.other_org, is_admin=False)

    def test_clinic_admin_can_update_own_organisation(self):
        self.client.force_authenticate(user=self.clinic_admin)

        response = self.client.patch(
            f"/api/users/admin/organisations/{self.org.pk}/",
            {"name": "Central Clinic Updated"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.org.refresh_from_db()
        self.assertEqual(self.org.name, "Central Clinic Updated")

    def test_clinic_admin_cannot_update_other_organisation(self):
        self.client.force_authenticate(user=self.clinic_admin)

        response = self.client.patch(
            f"/api/users/admin/organisations/{self.other_org.pk}/",
            {"name": "Forbidden"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_clinic_admin_can_update_therapist_in_own_organisation(self):
        self.client.force_authenticate(user=self.clinic_admin)

        response = self.client.patch(
            f"/api/users/admin/therapists/{self.therapist.pk}/",
            {"specialty": "Trauma"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.therapist.refresh_from_db()
        self.assertEqual(self.therapist.specialty, "Trauma")

    def test_clinic_admin_cannot_update_therapist_in_other_organisation(self):
        self.client.force_authenticate(user=self.clinic_admin)

        response = self.client.patch(
            f"/api/users/admin/therapists/{self.other_therapist.pk}/",
            {"specialty": "Forbidden"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_clinic_admin_can_soft_delete_own_organisation(self):
        self.client.force_authenticate(user=self.clinic_admin)

        response = self.client.delete(f"/api/users/admin/organisations/{self.org.pk}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.org.refresh_from_db()
        self.assertFalse(self.org.is_active)

    def test_clinic_admin_can_revoke_clinic_admin_role(self):
        self.client.force_authenticate(user=self.clinic_admin)

        response = self.client.patch(
            f"/api/users/admin/therapists/{self.second_admin.pk}/",
            {"is_admin": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        membership = OrganisationMember.objects.get(user=self.second_admin, organisation=self.org)
        self.assertFalse(membership.is_admin)
