from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
import pyotp
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import Patient, ProfessionalDirectoryEntry, Therapist, TherapistPatient, User


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
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com",
            password="AdminPass123!",
            first_name="Admin",
            last_name="User",
        )
        self.url = "/api/auth/register/therapist/"

    def test_register_therapist_successfully_for_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "first_name": "Laura",
            "last_name": "Gomez",
            "email": "laura@example.com",
            "license_number": "30809",
            "specialty": "Clinical Psychology",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Therapist.objects.count(), 1)
        therapist = Therapist.objects.get(email="laura@example.com")
        self.assertEqual(therapist.first_name, "Laura")
        self.assertEqual(therapist.license_number, "30809")
        self.assertFalse(therapist.is_active)
        self.assertFalse(therapist.has_usable_password())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("activate-account", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, ["laura@example.com"])
        self.assertNotIn("password", response.data)

    def test_register_therapist_requires_admin_user(self):
        payload = {
            "first_name": "Laura",
            "last_name": "Gomez",
            "email": "laura@example.com",
            "license_number": "30809",
            "specialty": "Clinical Psychology",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Therapist.objects.count(), 0)

    def test_register_therapist_rejects_unknown_license_number(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "first_name": "Laura",
            "last_name": "Gomez",
            "email": "laura@example.com",
            "license_number": "99999",
            "specialty": "Clinical Psychology",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("license_number", response.data)
        self.assertEqual(Therapist.objects.count(), 0)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_URL="http://localhost:5173",
)
class PatientRegistrationTests(APITestCase):
    def setUp(self):
        self.therapist = Therapist.objects.create_user(
            email="therapist@example.com",
            password="StrongPass123!",
            first_name="Marta",
            last_name="Lopez",
            license_number="16385",
            specialty="Clinical Psychology",
        )
        self.url = "/api/auth/register/patient/"

    def test_register_patient_successfully_for_therapist(self):
        self.client.force_authenticate(user=self.therapist)
        payload = {
            "first_name": "Pablo",
            "last_name": "Martin",
            "email": "pablo@example.com",
            "birth_date": "2000-05-10",
            "consent_accepted": True,
            "consent_date": "2026-03-29T12:00:00Z",
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
        self.therapist = Therapist.objects.create_user(
            email="therapist@example.com",
            password="StrongPass123!",
            first_name="Marta",
            last_name="Lopez",
            license_number="16385",
            specialty="Clinical Psychology",
            is_active=True,
        )
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
        TherapistPatient.objects.create(therapist=self.therapist, patient=self.patient)
        self.list_url = "/api/auth/patients/"
        self.register_url = "/api/auth/register/patient/"

    def test_therapist_can_list_assigned_patients(self):
        self.client.force_authenticate(user=self.therapist)

        response = self.client.get(self.list_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(self.patient.pk))
        self.assertEqual(response.data[0]["email"], self.patient.email)
        self.assertIn("email", response.data[0])
        self.assertEqual(Patient.objects.count(), 2)

    def test_register_patient_requires_consent_date_when_consent_accepted(self):
        self.client.force_authenticate(user=self.therapist)
        response = self.client.post(
            self.register_url,
            {
                "first_name": "Pablo",
                "last_name": "Martin",
                "email": "pablo@example.com",
                "birth_date": "2000-05-10",
                "consent_accepted": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("consent_date", response.data)
        self.assertEqual(Patient.objects.count(), 2)


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
        self.url = "/api/auth/activate/account/"

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
        self.therapist = Therapist.objects.create_user(
            email="therapist@example.com",
            password="StrongPass123!",
            first_name="Marta",
            last_name="Lopez",
            license_number="16385",
            specialty="Clinical Psychology",
        )
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
            is_active=False,
        )
        self.inactive_patient.set_password("StrongPass123!")
        self.inactive_patient.save(update_fields=["password", "is_active"])
        self.login_url = "/api/auth/login/"
        self.logout_url = "/api/auth/logout/"
        self.me_url = "/api/auth/me/"
        self.accept_consent_url = "/api/auth/consent/accept/"
        self.reject_consent_url = "/api/auth/consent/reject/"
        self.two_factor_setup_url = "/api/auth/2fa/setup/"
        self.two_factor_enable_url = "/api/auth/2fa/enable/"
        self.two_factor_verify_url = "/api/auth/2fa/verify/"
        self.two_factor_disable_url = "/api/auth/2fa/disable/"

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
        self.patient.consent_accepted = True
        self.patient.save(update_fields=["consent_accepted"])

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

    def test_login_requires_patient_consent_before_home(self):
        response = self.client.post(
            self.login_url,
            {"email": "patient@example.com", "password": "StrongPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["login_status"], "consent_required")
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

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

    def test_patient_can_accept_consent(self):
        refresh = RefreshToken.for_user(self.patient)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = self.client.post(self.accept_consent_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.patient.refresh_from_db()
        self.assertTrue(self.patient.consent_accepted)
        self.assertIsNotNone(self.patient.consent_date)

    def test_patient_can_reject_consent_and_account_becomes_inactive(self):
        refresh = RefreshToken.for_user(self.patient)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = self.client.post(
            self.reject_consent_url,
            {"refresh": str(refresh)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.patient.refresh_from_db()
        self.assertFalse(self.patient.consent_accepted)
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
        response = self.client.get("/api/auth/consent/document/")

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
        self.forgot_url = "/api/auth/password/forgot/"
        self.reset_url = "/api/auth/password/reset/"

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
        self.patient_me_url = "/api/auth/me/"
        self.change_password_url = "/api/auth/change-password/"
        self.delete_account_url = "/api/auth/delete-account/"
        self.patient_deactivate_url = "/api/auth/patients/deactivate/"

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
