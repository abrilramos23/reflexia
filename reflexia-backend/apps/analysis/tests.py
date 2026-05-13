from unittest.mock import patch

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.analysis.models import EmotionalAnalysis
from apps.entries.models import JournalEntry
from apps.users.models import Patient, Therapist, TherapistPatient


class AnalysisEndpointTests(APITestCase):
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
        TherapistPatient.objects.create(therapist=self.therapist, patient=self.patient)
        self.entry = JournalEntry.objects.create(
            patient=self.patient,
            content="<p>Avui em sento trista pero una mica esperancada.</p>",
        )

    def create_analysis(self, entry=None, primary_emotion="Tristesa", risk_level="low"):
        return EmotionalAnalysis.objects.create(
            entry=entry or self.entry,
            emotions=[
                {"emotion": primary_emotion, "percentage": 70},
                {"emotion": "Esperanca", "percentage": 30},
            ],
            primary_emotion=primary_emotion,
            risk_level=risk_level,
            summary="Predomina la tristesa amb elements d'esperanca.",
        )

    def test_patient_gets_pending_message_when_analysis_does_not_exist(self):
        self.client.force_authenticate(user=self.patient)

        response = self.client.get(f"/api/entries/{self.entry.pk}/analysis/")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIsNone(response.data["analysis"])

    def test_patient_can_consult_entry_analysis(self):
        self.create_analysis()
        self.client.force_authenticate(user=self.patient)

        response = self.client.get(f"/api/entries/{self.entry.pk}/analysis/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["primary_emotion"], "Tristesa")
        self.assertEqual(response.data["risk_level"], "low")
        self.assertIn("disclaimer", response.data)

    @patch("apps.entries.views.analyze_journal_entry")
    def test_patient_can_request_entry_analysis_generation(self, mocked_analyze):
        def create_mocked_analysis(entry):
            analysis = self.create_analysis(entry=entry)
            return analysis

        mocked_analyze.side_effect = create_mocked_analysis
        self.client.force_authenticate(user=self.patient)

        response = self.client.post(f"/api/entries/{self.entry.pk}/analyze/", {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["entry"]["analysis"]["primary_emotion"], "Tristesa")
        self.assertEqual(response.data["entry"]["status"], JournalEntry.STATUS_ACTIVE)

    def test_patient_evolution_is_chronological(self):
        older_entry = JournalEntry.objects.create(patient=self.patient, content="Primer text")
        older_entry.created_at = timezone.now() - timezone.timedelta(days=3)
        older_entry.save(update_fields=["created_at"])
        self.create_analysis(entry=older_entry, primary_emotion="Calma")
        self.create_analysis(entry=self.entry, primary_emotion="Tristesa")
        self.client.force_authenticate(user=self.patient)

        response = self.client.get("/api/analysis/evolution/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["has_enough_data"])
        self.assertEqual(response.data["data_points"][0]["primary_emotion"], "Calma")
        self.assertEqual(response.data["data_points"][1]["primary_emotion"], "Tristesa")

    def test_patient_evolution_includes_stacked_chart_aggregates(self):
        older_entry = JournalEntry.objects.create(patient=self.patient, content="Primer text")
        older_entry.created_at = timezone.now() - timezone.timedelta(days=3)
        older_entry.save(update_fields=["created_at"])
        self.create_analysis(entry=older_entry, primary_emotion="Calma", risk_level="none")
        self.create_analysis(entry=self.entry, primary_emotion="Tristesa", risk_level="high")
        self.client.force_authenticate(user=self.patient)

        response = self.client.get("/api/analysis/evolution/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["analyzed_entries_count"], 2)
        self.assertEqual(response.data["risk_counts"]["none"], 1)
        self.assertEqual(response.data["risk_counts"]["high"], 1)
        self.assertEqual(response.data["frequent_emotions"][0]["emotion"], "Esperanca")
        self.assertIn("emotions", response.data["data_points"][0])

    def test_therapist_can_correct_analysis_for_assigned_patient(self):
        self.create_analysis()
        self.client.force_authenticate(user=self.therapist)

        response = self.client.patch(
            f"/api/auth/patients/{self.patient.pk}/entries/{self.entry.pk}/analysis/",
            {"therapist_correction": "La lectura correcta es ansietat anticipatoria lleu."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["therapist_correction"],
            "La lectura correcta es ansietat anticipatoria lleu.",
        )
        self.assertTrue(response.data["reviewed_by_therapist"])

    def test_therapist_can_mark_analysis_reviewed_with_empty_correction(self):
        analysis = self.create_analysis()
        analysis.therapist_correction = "Correccio previa"
        analysis.save(update_fields=["therapist_correction"])
        self.client.force_authenticate(user=self.therapist)

        response = self.client.patch(
            f"/api/auth/patients/{self.patient.pk}/entries/{self.entry.pk}/analysis/",
            {"therapist_correction": "   "},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["therapist_correction"], "")
        self.assertIsNone(response.data["manual_corrections"])
        self.assertTrue(response.data["reviewed_by_therapist"])

    def test_unassigned_therapist_cannot_consult_patient_analysis(self):
        self.create_analysis()
        self.client.force_authenticate(user=self.other_therapist)

        response = self.client.get(
            f"/api/auth/patients/{self.patient.pk}/entries/{self.entry.pk}/analysis/"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
