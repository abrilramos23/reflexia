from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.entries.models import JournalEntry, TherapistQuestion
from apps.users.models import Patient, Therapist, TherapistPatient


class JournalEntryEditorTests(APITestCase):
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
        self.active_question = TherapistQuestion.objects.create(
            therapist=self.therapist,
            patient=self.patient,
            question="Quin moment de la setmana t’ha remogut més emocionalment?",
            is_active=True,
        )
        self.context_url = "/api/entries/editor/"
        self.entries_url = "/api/entries/"

    def test_patient_can_fetch_editor_context_with_active_question(self):
        self.client.force_authenticate(user=self.patient)

        response = self.client.get(self.context_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["active_question"]["id"], str(self.active_question.pk))
        self.assertEqual(response.data["active_question"]["question"], self.active_question.question)

    def test_patient_can_create_non_empty_draft(self):
        self.client.force_authenticate(user=self.patient)

        response = self.client.post(
            self.entries_url,
            {"content": "Avui m’he sentit més tranquil·la després de parlar amb la Marta Lopez."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(JournalEntry.objects.count(), 1)
        entry = JournalEntry.objects.get()
        self.assertEqual(entry.patient, self.patient)
        self.assertEqual(entry.status, JournalEntry.STATUS_DRAFT)
        self.assertEqual(entry.therapist_question, self.active_question)

    def test_patient_cannot_create_empty_entry(self):
        self.client.force_authenticate(user=self.patient)

        response = self.client.post(self.entries_url, {"content": "   "}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("content", response.data)

    def test_editing_deleted_entry_is_rejected(self):
        self.client.force_authenticate(user=self.patient)
        entry = JournalEntry.objects.create(
            patient=self.patient,
            content="Text inicial",
            deleted_at=timezone.now(),
        )

        response = self.client.patch(
            f"/api/entries/{entry.pk}/",
            {"content": "Text actualitzat"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    def test_patient_can_update_existing_entry(self):
        self.client.force_authenticate(user=self.patient)
        entry = JournalEntry.objects.create(
            patient=self.patient,
            therapist_question=self.active_question,
            content="Em sento cansada.",
        )

        patch_response = self.client.patch(
            f"/api/entries/{entry.pk}/",
            {"content": "Em sento cansada però amb una mica més d’esperança."},
            format="json",
        )

        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.data["status"], JournalEntry.STATUS_DRAFT)

    def test_patient_cannot_access_someone_elses_entry(self):
        entry = JournalEntry.objects.create(patient=self.other_patient, content="Privada")
        self.client.force_authenticate(user=self.patient)

        response = self.client.get(f"/api/entries/{entry.pk}/", format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patient_can_list_entries(self):
        self.client.force_authenticate(user=self.patient)
        JournalEntry.objects.create(patient=self.patient, content="<p>Primera entrada</p>")
        JournalEntry.objects.create(patient=self.patient, content="<p>Segona entrada</p>")

        response = self.client.get(self.entries_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertIn("preview", response.data[0])

    def test_delete_entry_soft_deletes_and_anonymizes(self):
        self.client.force_authenticate(user=self.patient)
        entry = JournalEntry.objects.create(
            patient=self.patient,
            therapist_question=self.active_question,
            content="<p>Text privat</p>",
        )

        response = self.client.delete(f"/api/entries/{entry.pk}/", format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        entry.refresh_from_db()
        self.assertTrue(entry.deleted_at is not None)
        self.assertEqual(entry.content, "Aquesta entrada ha estat eliminada i anonimitzada.")
        self.assertIsNone(entry.therapist_question)
