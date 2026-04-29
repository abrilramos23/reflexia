from rest_framework import status
from rest_framework.test import APITestCase

from apps.contacts.models import AssociatedContact, DefaultContact, SupportTherapist
from apps.users.models import Organisation, Patient, Therapist, OrganisationMember


class AssociatedContactTests(APITestCase):
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
        self.url = "/api/contacts/associated/"

    def test_patient_can_create_and_list_contacts(self):
        self.client.force_authenticate(user=self.patient)

        create_response = self.client.post(
            self.url,
            {
                "name": "Maria Perez",
                "relation": "Sister",
                "email": "maria@example.com",
                "is_default": True,
            },
            format="json",
        )

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            DefaultContact.objects.filter(
                patient=self.patient,
                contact_id=create_response.data["id"],
                is_default=True,
            ).exists()
        )
        list_response = self.client.get(self.url, format="json")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)

    def test_patient_contact_requires_email_or_phone(self):
        self.client.force_authenticate(user=self.patient)
        response = self.client.post(
            self.url,
            {
                "name": "Maria Perez",
                "relation": "Sister",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SupportTherapistTests(APITestCase):
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

        self.other_therapist = Therapist.objects.create_user(
            email="support@example.com",
            password="StrongPass123!",
            first_name="Joan",
            last_name="Serra",
            license_number="17105",
            specialty="Trauma Therapy",
            is_active=True,
        )
        OrganisationMember.objects.create(user=self.other_therapist, organisation=self.org, is_admin=False)
        self.url = "/api/contacts/support-therapists/"

    def test_therapist_can_add_and_list_support_therapists(self):
        self.client.force_authenticate(user=self.therapist)

        create_response = self.client.post(
            self.url,
            {"support_id": str(self.other_therapist.pk)},
            format="json",
        )

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.data["support_id"], str(self.other_therapist.pk))
        list_response = self.client.get(self.url, format="json")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)

    def test_therapist_cannot_add_self_as_support(self):
        self.client.force_authenticate(user=self.therapist)
        response = self.client.post(
            self.url,
            {"support_id": str(self.therapist.pk)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
