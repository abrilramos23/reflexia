from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import Patient, ProfessionalDirectoryEntry, Therapist, TherapistPatient, User


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
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "license_number": "30809",
            "specialty": "Clinical Psychology",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Therapist.objects.count(), 1)
        therapist = Therapist.objects.get(email="laura@example.com")
        self.assertEqual(therapist.first_name, "Laura")
        self.assertEqual(therapist.license_number, "30809")
        self.assertTrue(therapist.check_password("StrongPass123!"))
        self.assertNotIn("password", response.data)

    def test_register_therapist_requires_admin_user(self):
        payload = {
            "first_name": "Laura",
            "last_name": "Gomez",
            "email": "laura@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "license_number": "30809",
            "specialty": "Clinical Psychology",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Therapist.objects.count(), 0)

    def test_register_therapist_rejects_mismatched_passwords(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "first_name": "Laura",
            "last_name": "Gomez",
            "email": "laura@example.com",
            "password": "StrongPass123!",
            "password_confirm": "DifferentPass123!",
            "license_number": "30809",
            "specialty": "Clinical Psychology",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Therapist.objects.count(), 0)

    def test_register_therapist_rejects_weak_password(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "first_name": "Laura",
            "last_name": "Gomez",
            "email": "laura@example.com",
            "password": "weakpass",
            "password_confirm": "weakpass",
            "license_number": "30809",
            "specialty": "Clinical Psychology",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertEqual(Therapist.objects.count(), 0)

    def test_register_therapist_rejects_unknown_license_number(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "first_name": "Laura",
            "last_name": "Gomez",
            "email": "laura@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
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

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
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
        self.assertIn("email", response.data)
        self.assertEqual(Patient.objects.count(), 0)

    def test_register_patient_requires_consent_date_when_consent_accepted(self):
        self.client.force_authenticate(user=self.therapist)
        response = self.client.post(
            self.url,
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
        self.assertEqual(Patient.objects.count(), 0)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PatientActivationTests(APITestCase):
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
        self.url = "/api/auth/activate/patient/"

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
