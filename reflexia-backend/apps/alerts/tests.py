import uuid
from django.test import TestCase
from django.utils import timezone

from apps.users.models import User, Patient, Therapist
from apps.entries.models import JournalEntry
from apps.analysis.models import EmotionalAnalysis
from apps.alerts.models import Alert, AlertNotification


class AlertAutoGenerationTestCase(TestCase):
    def setUp(self):
        self.therapist = Therapist.objects.create_user(
            email="therapist@test.com",
            password="test123",
            first_name="John",
            last_name="Therapist",
            license_number="LIC123",
            specialty="Psychology",
        )

        self.patient = Patient.objects.create_user(
            email="patient@test.com",
            password="test123",
            first_name="Jane",
            last_name="Patient",
            birth_date="1990-01-01",
        )

    def test_alert_created_on_high_risk_analysis(self):
        journal_entry = JournalEntry.objects.create(
            patient=self.patient,
            content="Test entry content",
        )

        analysis = EmotionalAnalysis.objects.create(
            entry=journal_entry,
            risk_level=EmotionalAnalysis.HIGH,
            primary_emotion="sadness",
            summary="High risk detected",
            emotions={"sadness": 0.8, "anxiety": 0.6},
        )

        alert = Alert.objects.filter(emotional_analysis=analysis).first()
        self.assertIsNotNone(alert)
        self.assertEqual(alert.status, Alert.Status.PENDING)
        self.assertEqual(alert.risk_level, EmotionalAnalysis.HIGH)
        self.assertEqual(alert.patient, self.patient)

    def test_no_alert_created_on_low_risk(self):
        journal_entry = JournalEntry.objects.create(
            patient=self.patient,
            content="Test entry content",
        )

        analysis = EmotionalAnalysis.objects.create(
            entry=journal_entry,
            risk_level=EmotionalAnalysis.LOW,
            primary_emotion="happiness",
            summary="Low risk",
            emotions={"happiness": 0.7},
        )

        alert = Alert.objects.filter(emotional_analysis=analysis).first()
        self.assertIsNone(alert)

    def test_alert_validation(self):
        journal_entry = JournalEntry.objects.create(
            patient=self.patient,
            content="Test entry",
        )

        analysis = EmotionalAnalysis.objects.create(
            entry=journal_entry,
            risk_level=EmotionalAnalysis.HIGH,
            primary_emotion="anxiety",
            summary="High anxiety detected",
            emotions={"anxiety": 0.9},
        )

        alert = Alert.objects.get(emotional_analysis=analysis)

        alert.status = Alert.Status.VALIDATED
        alert.validating_therapist = self.therapist
        alert.validation_note = "Patient needs immediate support"
        alert.validated_at = timezone.now()
        alert.save()

        alert.refresh_from_db()
        self.assertEqual(alert.status, Alert.Status.VALIDATED)
        self.assertIsNotNone(alert.validated_at)
        self.assertIn("immediate support", alert.validation_note)

    def test_alert_query_filters(self):
        for i in range(3):
            journal_entry = JournalEntry.objects.create(
                patient=self.patient,
                content=f"Entry {i}",
            )

            EmotionalAnalysis.objects.create(
                entry=journal_entry,
                risk_level=EmotionalAnalysis.HIGH,
                primary_emotion="sadness",
                summary=f"Analysis {i}",
                emotions={"sadness": 0.7 + i * 0.1},
            )

        all_alerts = Alert.objects.all()
        self.assertEqual(all_alerts.count(), 3)

        pending = Alert.objects.filter(status=Alert.Status.PENDING)
        self.assertEqual(pending.count(), 3)

        first_alert = all_alerts.first()
        first_alert.status = Alert.Status.VALIDATED
        first_alert.save()

        validated = Alert.objects.filter(status=Alert.Status.VALIDATED)
        self.assertEqual(validated.count(), 1)
        pending = Alert.objects.filter(status=Alert.Status.PENDING)
        self.assertEqual(pending.count(), 2)

    def test_alert_created_on_high_risk_analysis(self):
        journal_entry = JournalEntry.objects.create(
            patient=self.patient,
            content="Test entry content",
        )

        analysis = EmotionalAnalysis.objects.create(
            entry=journal_entry,
            risk_level=EmotionalAnalysis.HIGH,
            primary_emotion="sadness",
            summary="High risk detected",
            emotions={"sadness": 0.8, "anxiety": 0.6},
        )

        alert = Alert.objects.filter(emotional_analysis=analysis).first()
        self.assertIsNotNone(alert)
        self.assertEqual(alert.status, Alert.Status.PENDING)
        self.assertEqual(alert.risk_level, EmotionalAnalysis.HIGH)
        self.assertEqual(alert.patient, self.patient)

    def test_no_alert_created_on_low_risk(self):
        journal_entry = JournalEntry.objects.create(
            patient=self.patient,
            content="Test entry content",
        )

        analysis = EmotionalAnalysis.objects.create(
            entry=journal_entry,
            risk_level=EmotionalAnalysis.LOW,
            primary_emotion="happiness",
            summary="Low risk",
            emotions={"happiness": 0.7},
        )

        alert = Alert.objects.filter(emotional_analysis=analysis).first()
        self.assertIsNone(alert)

    def test_alert_validation(self):
        journal_entry = JournalEntry.objects.create(
            patient=self.patient,
            content="Test entry",
        )

        analysis = EmotionalAnalysis.objects.create(
            entry=journal_entry,
            risk_level=EmotionalAnalysis.HIGH,
            primary_emotion="anxiety",
            summary="High anxiety detected",
            emotions={"anxiety": 0.9},
        )

        alert = Alert.objects.get(emotional_analysis=analysis)

        alert.status = Alert.Status.VALIDATED
        alert.validating_therapist = self.therapist
        alert.validation_note = "Patient needs immediate support"
        alert.validated_at = timezone.now()
        alert.save()

        alert.refresh_from_db()
        self.assertEqual(alert.status, Alert.Status.VALIDATED)
        self.assertIsNotNone(alert.validated_at)
        self.assertIn("immediate support", alert.validation_note)

    def test_alert_query_filters(self):
        for i in range(3):
            journal_entry = JournalEntry.objects.create(
                patient=self.patient,
                content=f"Entry {i}",
            )

            EmotionalAnalysis.objects.create(
                entry=journal_entry,
                risk_level=EmotionalAnalysis.HIGH,
                primary_emotion="sadness",
                summary=f"Analysis {i}",
                emotions={"sadness": 0.7 + i * 0.1},
            )

        all_alerts = Alert.objects.all()
        self.assertEqual(all_alerts.count(), 3)

        pending = Alert.objects.filter(status=Alert.Status.PENDING)
        self.assertEqual(pending.count(), 3)

        first_alert = all_alerts.first()
        first_alert.status = Alert.Status.VALIDATED
        first_alert.save()

        validated = Alert.objects.filter(status=Alert.Status.VALIDATED)
        self.assertEqual(validated.count(), 1)
        pending = Alert.objects.filter(status=Alert.Status.PENDING)
        self.assertEqual(pending.count(), 2)
