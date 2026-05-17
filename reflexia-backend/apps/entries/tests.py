from rest_framework import status
from rest_framework.test import APITestCase

from apps.analysis.models import EmotionalAnalysis
from apps.entries.models import JournalEntry, PrivateNote, TherapistQuestion
from apps.users.models import Patient, Therapist, TherapistPatient


class EntriesPatientFlowTests(APITestCase):
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
        self.assertFalse(response.data["active_question"]["resolved"])

    def test_patient_can_create_non_empty_draft_and_resolve_active_question(self):
        self.client.force_authenticate(user=self.patient)

        response = self.client.post(
            self.entries_url,
            {"content": "Avui m’he sentit més tranquil·la després de parlar amb la Marta Lopez."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        entry = JournalEntry.objects.get()
        self.assertEqual(entry.patient, self.patient)
        self.assertEqual(entry.status, JournalEntry.STATUS_ACTIVE)
        self.assertEqual(entry.therapist_question, self.active_question)
        self.active_question.refresh_from_db()
        self.assertFalse(self.active_question.is_active)

    def test_patient_cannot_create_empty_entry(self):
        self.client.force_authenticate(user=self.patient)

        response = self.client.post(self.entries_url, {"content": "   "}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("content", response.data)

    def test_patient_can_update_existing_entry_and_modification_date_is_returned(self):
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
        self.assertEqual(patch_response.data["status"], JournalEntry.STATUS_MODIFIED)

    def test_patient_cannot_access_deleted_entry_in_list_or_detail(self):
        self.client.force_authenticate(user=self.patient)
        visible_entry = JournalEntry.objects.create(patient=self.patient, content="Visible")
        deleted_entry = JournalEntry.objects.create(
            patient=self.patient,
            content="Privada",
            status=JournalEntry.STATUS_DELETED,
        )

        list_response = self.client.get(self.entries_url, format="json")
        detail_response = self.client.get(f"/api/entries/{deleted_entry.pk}/", format="json")

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]["id"], str(visible_entry.pk))
        self.assertEqual(detail_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_entry_soft_deletes_hides_and_anonymizes(self):
        self.client.force_authenticate(user=self.patient)
        entry = JournalEntry.objects.create(
            patient=self.patient,
            therapist_question=self.active_question,
            content="<p>Text privat</p>",
        )
        EmotionalAnalysis.objects.create(
            entry=entry,
            emotions=[{"emotion": "Tristesa", "percentage": 70}],
            primary_emotion="Tristesa",
            risk_level="low",
            summary="Predomina la tristesa.",
        )

        response = self.client.delete(f"/api/entries/{entry.pk}/", format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("retention_explanation", response.data)
        entry.refresh_from_db()
        self.assertEqual(entry.status, JournalEntry.STATUS_DELETED)
        self.assertEqual(entry.content, "Aquesta entrada ha estat eliminada i anonimitzada.")
        self.assertFalse(hasattr(entry, "analysis"))

    def test_patient_can_export_single_entry_pdf(self):
        self.client.force_authenticate(user=self.patient)
        entry = JournalEntry.objects.create(patient=self.patient, content="Text exportable")

        response = self.client.get(f"/api/entries/{entry.pk}/export/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))


class TherapistEntriesAndQuestionsTests(APITestCase):
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
        self.other_therapist = Therapist.objects.create_user(
            email="other-therapist@example.com",
            password="StrongPass123!",
            first_name="Pere",
            last_name="Soler",
            license_number="99999",
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
        self.entry = JournalEntry.objects.create(
            patient=self.patient,
            content="<p>Entrada del pacient</p>",
        )
        self.question = TherapistQuestion.objects.create(
            therapist=self.therapist,
            patient=self.patient,
            question="Com t'has sentit aquesta setmana?",
            is_active=True,
        )

    def test_therapist_can_list_assigned_patient_entries(self):
        self.client.force_authenticate(user=self.therapist)

        response = self.client.get(f"/api/entries/patients/{self.patient.pk}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn("content", response.data[0])

    def test_therapist_cannot_list_entries_of_unassigned_patient(self):
        self.client.force_authenticate(user=self.therapist)

        response = self.client.get(f"/api/entries/patients/{self.other_patient.pk}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_therapist_can_create_question_for_assigned_patient(self):
        self.client.force_authenticate(user=self.therapist)

        response = self.client.post(
            f"/api/entries/patients/{self.patient.pk}/questions/",
            {"text": "Quina situació t'ha generat més ansietat avui?"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.question.refresh_from_db()
        self.assertFalse(self.question.is_active)
        self.assertEqual(response.data["question"]["question"], "Quina situació t'ha generat més ansietat avui?")

    def test_therapist_all_questions_lists_only_own_questions_with_patient_context(self):
        other_question = TherapistQuestion.objects.create(
            therapist=self.other_therapist,
            patient=self.other_patient,
            question="Pregunta d'un altre terapeuta",
            is_active=True,
        )
        self.client.force_authenticate(user=self.therapist)

        response = self.client.get("/api/entries/questions/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        question_ids = {item["id"] for item in response.data}
        self.assertIn(str(self.question.pk), question_ids)
        self.assertNotIn(str(other_question.pk), question_ids)
        self.assertEqual(response.data[0]["patient_id"], str(self.patient.pk))
        self.assertEqual(response.data[0]["patient_name"], "Paula Sanchez")

    def test_therapist_can_add_and_list_private_notes(self):
        self.client.force_authenticate(user=self.therapist)

        create_response = self.client.post(
            f"/api/entries/patients/{self.patient.pk}/{self.entry.pk}/notes/",
            {"content": "Valorar si hi ha un patró d'evitació després de la propera sessió."},
            format="json",
        )
        list_response = self.client.get(f"/api/entries/patients/{self.patient.pk}/{self.entry.pk}/notes/")

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PrivateNote.objects.count(), 1)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]["content"], "Valorar si hi ha un patró d'evitació després de la propera sessió.")

    def test_other_therapist_cannot_access_private_notes_of_unassigned_patient(self):
        self.client.force_authenticate(user=self.other_therapist)

        response = self.client.get(f"/api/entries/patients/{self.patient.pk}/{self.entry.pk}/notes/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
