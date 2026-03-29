from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import Therapist, User


class TherapistRegistrationTests(APITestCase):
    def setUp(self):
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
            "license_number": "COL-12345",
            "specialty": "Clinical Psychology",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Therapist.objects.count(), 1)
        therapist = Therapist.objects.get(email="laura@example.com")
        self.assertEqual(therapist.first_name, "Laura")
        self.assertEqual(therapist.license_number, "COL-12345")
        self.assertTrue(therapist.check_password("StrongPass123!"))
        self.assertNotIn("password", response.data)

    def test_register_therapist_requires_admin_user(self):
        payload = {
            "first_name": "Laura",
            "last_name": "Gomez",
            "email": "laura@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "license_number": "COL-12345",
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
            "license_number": "COL-12345",
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
            "license_number": "COL-12345",
            "specialty": "Clinical Psychology",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertEqual(Therapist.objects.count(), 0)
