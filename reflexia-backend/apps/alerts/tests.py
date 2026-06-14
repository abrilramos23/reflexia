from datetime import datetime

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from unittest.mock import patch
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import Organisation, OrganisationMember, Patient, Therapist, TherapistPatient
from apps.entries.models import JournalEntry
from apps.analysis.models import EmotionalAnalysis
from apps.alerts.models import Alert
from apps.alerts.serializers import AlertDetailSerializer
from apps.alerts.services import send_alert_email_to_contact
from apps.alerts.tasks import escalate_pending_alerts, send_inactivity_reminders
from apps.contacts.models import AssociatedContact, DefaultContact, SupportTherapist


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


class AlertAPITestCase(APITestCase):
    def setUp(self):
        self.therapist = Therapist.objects.create_user(
            email="therapist@example.com",
            password="StrongPass123!",
            first_name="Marta",
            last_name="Lopez",
            license_number="T-001",
            specialty="Clinical Psychology",
            is_active=True,
        )
        self.other_therapist = Therapist.objects.create_user(
            email="other-therapist@example.com",
            password="StrongPass123!",
            first_name="Joan",
            last_name="Serra",
            license_number="T-002",
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
            email="other-patient@example.com",
            password="StrongPass123!",
            first_name="Nil",
            last_name="Costa",
            birth_date="1999-04-12",
            is_active=True,
        )
        self.inactive_patient = Patient.objects.create_user(
            email="inactive-patient@example.com",
            password="StrongPass123!",
            first_name="Laia",
            last_name="Vila",
            birth_date="1998-08-23",
            is_active=True,
        )
        TherapistPatient.objects.create(therapist=self.therapist, patient=self.patient)
        TherapistPatient.objects.create(therapist=self.other_therapist, patient=self.other_patient)
        TherapistPatient.objects.create(
            therapist=self.therapist,
            patient=self.inactive_patient,
            is_active=False,
        )

        self.alert = self._create_alert(self.patient, risk_level=EmotionalAnalysis.HIGH)
        self.other_alert = self._create_alert(self.other_patient, risk_level=EmotionalAnalysis.HIGH)
        self.inactive_link_alert = self._create_alert(
            self.inactive_patient,
            risk_level=EmotionalAnalysis.HIGH,
        )

    def _create_alert(self, patient, risk_level=EmotionalAnalysis.HIGH, status_value=Alert.Status.PENDING):
        entry = JournalEntry.objects.create(
            patient=patient,
            content="Avui m'he sentit sobrepassada.",
        )
        analysis = EmotionalAnalysis.objects.create(
            entry=entry,
            risk_level=risk_level,
            primary_emotion="sadness",
            summary="High risk detected",
            emotions={"sadness": 0.8},
            recommendations=["Contactar amb el pacient"],
        )
        alert = Alert.objects.get(emotional_analysis=analysis)
        if alert.status != status_value:
            alert.status = status_value
            alert.save(update_fields=["status"])
        return alert

    def test_therapist_lists_only_alerts_for_active_assigned_patients(self):
        self.client.force_authenticate(user=self.therapist)

        response = self.client.get("/api/alerts/", format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        alert_ids = {item["id"] for item in response.data}
        self.assertIn(str(self.alert.pk), alert_ids)
        self.assertNotIn(str(self.other_alert.pk), alert_ids)
        self.assertNotIn(str(self.inactive_link_alert.pk), alert_ids)

    def test_therapist_can_filter_alerts_by_status_risk_and_patient(self):
        validated_alert = self._create_alert(
            self.patient,
            risk_level=EmotionalAnalysis.HIGH,
            status_value=Alert.Status.VALIDATED,
        )
        self.client.force_authenticate(user=self.therapist)

        response = self.client.get(
            "/api/alerts/",
            {
                "status": Alert.Status.VALIDATED,
                "risk_level": EmotionalAnalysis.HIGH,
                "patient_id": str(self.patient.pk),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [str(validated_alert.pk)])

    def test_therapist_cannot_fetch_alert_for_unassigned_patient(self):
        self.client.force_authenticate(user=self.therapist)

        response = self.client.get(f"/api/alerts/{self.other_alert.pk}/", format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_support_therapist_can_fetch_high_escalated_pending_alert_read_only(self):
        support_contact = AssociatedContact.objects.create(
            name="Maria Perez",
            email="maria-support@example.com",
            relation="Sister",
        )
        DefaultContact.objects.create(patient=self.patient, contact=support_contact, is_default=True)
        SupportTherapist.objects.create(
            therapist=self.therapist,
            support=self.other_therapist,
            status=SupportTherapist.Status.ACCEPTED,
        )
        self.alert.escalation_level = 3
        self.alert.save(update_fields=["escalation_level"])
        self.client.force_authenticate(user=self.other_therapist)

        response = self.client.get(f"/api/alerts/{self.alert.pk}/", format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.alert.pk))
        self.assertFalse(response.data["can_manage"])
        self.assertEqual(response.data["associated_contacts"], [])
        self.assertEqual(response.data["patient_name"], "Paula Sanchez")
        self.assertEqual(response.data["entry_content"], "Avui m'he sentit sobrepassada.")

    def test_support_therapist_cannot_fetch_alert_until_it_is_high_escalated_and_pending(self):
        SupportTherapist.objects.create(
            therapist=self.therapist,
            support=self.other_therapist,
            status=SupportTherapist.Status.ACCEPTED,
        )
        self.client.force_authenticate(user=self.other_therapist)

        response = self.client.get(f"/api/alerts/{self.alert.pk}/", format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.alert.escalation_level = 3
        self.alert.status = Alert.Status.VALIDATED
        self.alert.save(update_fields=["escalation_level", "status"])

        response = self.client.get(f"/api/alerts/{self.alert.pk}/", format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_support_therapist_cannot_manage_or_list_supported_alerts(self):
        SupportTherapist.objects.create(
            therapist=self.therapist,
            support=self.other_therapist,
            status=SupportTherapist.Status.ACCEPTED,
        )
        self.alert.escalation_level = 3
        self.alert.save(update_fields=["escalation_level"])
        self.client.force_authenticate(user=self.other_therapist)

        list_response = self.client.get("/api/alerts/", format="json")
        patch_response = self.client.patch(
            f"/api/alerts/{self.alert.pk}/",
            {
                "action": "VALIDATE",
                "justification": "Cal activar suport proper.",
            },
            format="json",
        )

        alert_ids = {item["id"] for item in list_response.data}
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertNotIn(str(self.alert.pk), alert_ids)
        self.assertIn(str(self.other_alert.pk), alert_ids)
        self.assertEqual(patch_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patient_cannot_use_therapist_alert_list(self):
        self.client.force_authenticate(user=self.patient)

        response = self.client.get("/api/alerts/", format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_therapist_can_validate_alert_through_endpoint(self):
        self.client.force_authenticate(user=self.therapist)

        response = self.client.patch(
            f"/api/alerts/{self.alert.pk}/",
            {
                "action": "VALIDATE",
                "validation_note": "Cal fer seguiment avui.",
                "justification": "El contingut descriu risc alt i cal activar suport proper.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, Alert.Status.VALIDATED)
        self.assertEqual(self.alert.validating_therapist, self.therapist)
        self.assertEqual(self.alert.validation_note, "Cal fer seguiment avui.")
        self.assertEqual(
            self.alert.justification,
            "El contingut descriu risc alt i cal activar suport proper.",
        )
        self.assertIsNotNone(self.alert.validated_at)

    def test_therapist_cannot_validate_alert_without_justification(self):
        self.client.force_authenticate(user=self.therapist)

        response = self.client.patch(
            f"/api/alerts/{self.alert.pk}/",
            {
                "action": "VALIDATE",
                "validation_note": "Cal fer seguiment avui.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, Alert.Status.PENDING)
        self.assertEqual(self.alert.justification, "")

    def test_therapist_can_dismiss_alert_through_endpoint(self):
        self.client.force_authenticate(user=self.therapist)

        response = self.client.patch(
            f"/api/alerts/{self.alert.pk}/",
            {"action": "DISMISS"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, Alert.Status.DISMISSED)
        self.assertEqual(self.alert.validating_therapist, self.therapist)
        self.assertIsNotNone(self.alert.validated_at)

    def test_patient_alert_list_only_returns_validated_own_alerts(self):
        self.alert.status = Alert.Status.VALIDATED
        self.alert.save(update_fields=["status"])
        self._create_alert(self.patient, risk_level=EmotionalAnalysis.HIGH)
        self.client.force_authenticate(user=self.patient)

        response = self.client.get("/api/alerts/my-alerts/", format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [str(self.alert.pk)])


class AlertNotificationAPITestCase(APITestCase):
    def setUp(self):
        self.therapist = Therapist.objects.create_user(
            email="therapist-notify@example.com",
            password="StrongPass123!",
            first_name="Marta",
            last_name="Lopez",
            license_number="N-001",
            specialty="Clinical Psychology",
            is_active=True,
        )
        self.patient = Patient.objects.create_user(
            email="patient-notify@example.com",
            password="StrongPass123!",
            first_name="Paula",
            last_name="Sanchez",
            birth_date="2001-01-10",
            is_active=True,
        )
        self.other_patient = Patient.objects.create_user(
            email="other-notify@example.com",
            password="StrongPass123!",
            first_name="Nil",
            last_name="Costa",
            birth_date="1999-04-12",
            is_active=True,
        )
        TherapistPatient.objects.create(therapist=self.therapist, patient=self.patient)
        self.alert = self._create_alert(self.patient)
        self.contact = AssociatedContact.objects.create(
            name="Maria Perez",
            email="maria@example.com",
            relation="Sister",
        )
        self.other_contact = AssociatedContact.objects.create(
            name="Pere Costa",
            email="pere@example.com",
            relation="Friend",
        )
        DefaultContact.objects.create(patient=self.patient, contact=self.contact, is_default=True)
        DefaultContact.objects.create(patient=self.other_patient, contact=self.other_contact, is_default=True)

    def _create_alert(self, patient):
        entry = JournalEntry.objects.create(patient=patient, content="Necessito ajuda.")
        analysis = EmotionalAnalysis.objects.create(
            entry=entry,
            risk_level=EmotionalAnalysis.HIGH,
            primary_emotion="anxiety",
            summary="High anxiety detected",
            emotions={"anxiety": 0.9},
        )
        return Alert.objects.get(emotional_analysis=analysis)

    def test_cannot_notify_contacts_for_pending_alert(self):
        self.client.force_authenticate(user=self.therapist)

        response = self.client.post(
            f"/api/alerts/{self.alert.pk}/notify-contacts/",
            {
                "contact_ids": [str(self.contact.pk)],
                "justification": "Cal activar el contacte de suport per risc alt.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("apps.alerts.tasks.batch_send_alerts_to_contacts.delay")
    def test_notify_contacts_enqueues_only_patient_contacts_and_marks_alert(self, delay_mock):
        self.alert.status = Alert.Status.VALIDATED
        self.alert.save(update_fields=["status"])
        self.client.force_authenticate(user=self.therapist)

        response = self.client.post(
            f"/api/alerts/{self.alert.pk}/notify-contacts/",
            {
                "contact_ids": [str(self.contact.pk), str(self.other_contact.pk)],
                "justification": "Cal activar el contacte de suport per risc alt.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["notified_count"], 1)
        delay_mock.assert_called_once_with(str(self.alert.pk), [str(self.contact.pk)])
        self.alert.refresh_from_db()
        self.assertEqual(
            self.alert.justification,
            "Cal activar el contacte de suport per risc alt.",
        )
        self.assertEqual(self.alert.notification_status, Alert.NotificationStatus.NOTIFIED)
        self.assertIsNotNone(self.alert.last_notified_at)

    def test_notify_contacts_requires_justification(self):
        self.alert.status = Alert.Status.VALIDATED
        self.alert.save(update_fields=["status"])
        self.client.force_authenticate(user=self.therapist)

        response = self.client.post(
            f"/api/alerts/{self.alert.pk}/notify-contacts/",
            {"contact_ids": [str(self.contact.pk)], "justification": "   "},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.notification_status, Alert.NotificationStatus.NOT_NOTIFIED)

    def test_notify_contacts_rejects_contacts_not_linked_to_patient(self):
        self.alert.status = Alert.Status.VALIDATED
        self.alert.save(update_fields=["status"])
        self.client.force_authenticate(user=self.therapist)

        response = self.client.post(
            f"/api/alerts/{self.alert.pk}/notify-contacts/",
            {
                "contact_ids": [str(self.other_contact.pk)],
                "justification": "Cal activar el contacte de suport per risc alt.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.notification_status, Alert.NotificationStatus.NOT_NOTIFIED)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_contact_email_includes_alert_justification(self):
        self.alert.justification = "La pacient ha expressat risc alt i necessita suport immediat."
        self.alert.save(update_fields=["justification"])

        send_alert_email_to_contact(self.alert, self.contact)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Justificació de la notificació", mail.outbox[0].body)
        self.assertIn(self.alert.justification, mail.outbox[0].body)


class AlertSerializerTestCase(TestCase):
    def test_detail_serializer_truncates_entry_content_and_includes_default_contacts(self):
        patient = Patient.objects.create_user(
            email="serializer-patient@example.com",
            password="StrongPass123!",
            first_name="Paula",
            last_name="Sanchez",
            birth_date="2001-01-10",
            is_active=True,
        )
        contact = AssociatedContact.objects.create(
            name="Maria Perez",
            email="maria@example.com",
            relation="Sister",
        )
        DefaultContact.objects.create(patient=patient, contact=contact, is_default=True)
        entry = JournalEntry.objects.create(patient=patient, content="x" * 501)
        analysis = EmotionalAnalysis.objects.create(
            entry=entry,
            risk_level=EmotionalAnalysis.HIGH,
            primary_emotion="sadness",
            summary="High risk detected",
            emotions={"sadness": 0.8},
        )
        alert = Alert.objects.get(emotional_analysis=analysis)

        data = AlertDetailSerializer(alert).data

        self.assertEqual(data["entry_content"], "x" * 500 + "...")
        self.assertEqual(len(data["associated_contacts"]), 1)
        self.assertEqual(data["associated_contacts"][0]["id"], str(contact.pk))


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class InactivityReminderTaskTestCase(TestCase):
    def _create_patient(self, email, reference_date):
        return Patient.objects.create_user(
            email=email,
            password="StrongPass123!",
            first_name="Paula",
            last_name="Sanchez",
            birth_date="2001-01-10",
            is_active=True,
            legal_terms_accepted=True,
            legal_terms_accepted_at=reference_date,
        )

    def _create_entry(self, patient, created_at):
        entry = JournalEntry.objects.create(patient=patient, content="Text")
        JournalEntry.objects.filter(pk=entry.pk).update(
            created_at=created_at,
            updated_at=created_at,
        )
        entry.refresh_from_db()
        return entry

    def test_sends_reminder_on_third_calendar_day_without_waiting_full_72_hours(self):
        now = timezone.make_aware(datetime(2026, 6, 12, 10, 0))
        last_entry_date = now - timezone.timedelta(days=3) + timezone.timedelta(hours=1)
        patient = self._create_patient("inactive@example.com", now - timezone.timedelta(days=10))
        self._create_entry(patient, last_entry_date)

        with patch("apps.alerts.tasks.timezone.now", return_value=now):
            reminders_sent = send_inactivity_reminders()

        self.assertEqual(reminders_sent, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [patient.email])
        self.assertIn("fa 3 dies", mail.outbox[0].body)
        self.assertIn("09/06/2026", mail.outbox[0].body)

    def test_sends_reminder_to_patient_who_has_never_written(self):
        now = timezone.make_aware(datetime(2026, 6, 12, 10, 0))
        patient = self._create_patient(
            "never-written@example.com",
            now - timezone.timedelta(days=3),
        )

        with patch("apps.alerts.tasks.timezone.now", return_value=now):
            reminders_sent = send_inactivity_reminders()

        self.assertEqual(reminders_sent, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [patient.email])
        self.assertIn("Encara no consta cap entrada", mail.outbox[0].body)

    def test_does_not_send_before_third_calendar_day(self):
        now = timezone.make_aware(datetime(2026, 6, 12, 10, 0))
        last_entry_date = now - timezone.timedelta(days=2)
        patient = self._create_patient("recent@example.com", now - timezone.timedelta(days=10))
        self._create_entry(patient, last_entry_date)

        with patch("apps.alerts.tasks.timezone.now", return_value=now):
            reminders_sent = send_inactivity_reminders()

        self.assertEqual(reminders_sent, 0)
        self.assertEqual(len(mail.outbox), 0)


class AlertEscalationTaskTestCase(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create_user(
            email="escalation-patient@example.com",
            password="StrongPass123!",
            first_name="Paula",
            last_name="Sanchez",
            birth_date="2001-01-10",
            is_active=True,
        )
        self.therapist = Therapist.objects.create_user(
            email="escalation-therapist@example.com",
            password="StrongPass123!",
            first_name="Marta",
            last_name="Lopez",
            license_number="ESC-001",
            specialty="Clinical Psychology",
            is_active=True,
        )
        TherapistPatient.objects.create(therapist=self.therapist, patient=self.patient)

    def _create_alert(self, created_at, status_value=Alert.Status.PENDING, escalation_level=0):
        entry = JournalEntry.objects.create(patient=self.patient, content="Text")
        analysis = EmotionalAnalysis.objects.create(
            entry=entry,
            risk_level=EmotionalAnalysis.HIGH,
            primary_emotion="sadness",
            summary="High risk detected",
            emotions={"sadness": 0.8},
        )
        alert = Alert.objects.get(emotional_analysis=analysis)
        Alert.objects.filter(pk=alert.pk).update(
            created_at=created_at,
            status=status_value,
            escalation_level=escalation_level,
            last_escalation_at=None,
        )
        alert.refresh_from_db()
        return alert

    def test_escalates_pending_alerts_across_time_thresholds(self):
        now = timezone.now()
        level_one = self._create_alert(now - timezone.timedelta(hours=2))
        level_two = self._create_alert(now - timezone.timedelta(hours=5))
        level_three = self._create_alert(now - timezone.timedelta(hours=25))

        escalate_pending_alerts()

        level_one.refresh_from_db()
        level_two.refresh_from_db()
        level_three.refresh_from_db()
        self.assertEqual(level_one.escalation_level, 1)
        self.assertEqual(level_two.escalation_level, 2)
        self.assertEqual(level_three.escalation_level, 3)
        self.assertIsNotNone(level_one.last_escalation_at)
        self.assertIsNotNone(level_two.last_escalation_at)
        self.assertIsNotNone(level_three.last_escalation_at)

    def test_escalation_ignores_non_pending_alerts(self):
        validated = self._create_alert(
            timezone.now() - timezone.timedelta(hours=25),
            status_value=Alert.Status.VALIDATED,
        )
        dismissed = self._create_alert(
            timezone.now() - timezone.timedelta(hours=25),
            status_value=Alert.Status.DISMISSED,
        )

        escalate_pending_alerts()

        validated.refresh_from_db()
        dismissed.refresh_from_db()
        self.assertEqual(validated.escalation_level, 0)
        self.assertEqual(dismissed.escalation_level, 0)
        self.assertIsNone(validated.last_escalation_at)
        self.assertIsNone(dismissed.last_escalation_at)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_escalation_sends_email_to_assigned_therapist(self):
        alert = self._create_alert(timezone.now() - timezone.timedelta(hours=2))

        escalate_pending_alerts()

        alert.refresh_from_db()
        self.assertEqual(alert.escalation_level, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.therapist.email])
        self.assertIn("nivell 1", mail.outbox[0].subject.lower())
        self.assertIn(str(alert.pk), mail.outbox[0].body)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_high_escalation_sends_email_to_support_therapists(self):
        organisation = Organisation.objects.create(
            name="Escalation Clinic",
            type=Organisation.Type.CLINIC,
        )
        OrganisationMember.objects.create(
            user=self.therapist,
            organisation=organisation,
            is_admin=True,
        )
        accepted_support = Therapist.objects.create_user(
            email="accepted-support@example.com",
            password="StrongPass123!",
            first_name="Joan",
            last_name="Serra",
            license_number="ESC-002",
            specialty="Trauma Therapy",
            is_active=True,
        )
        pending_support = Therapist.objects.create_user(
            email="pending-support@example.com",
            password="StrongPass123!",
            first_name="Laia",
            last_name="Vila",
            license_number="ESC-003",
            specialty="Clinical Psychology",
            is_active=True,
        )
        OrganisationMember.objects.create(
            user=accepted_support,
            organisation=organisation,
        )
        OrganisationMember.objects.create(
            user=pending_support,
            organisation=organisation,
        )
        SupportTherapist.objects.create(
            therapist=self.therapist,
            support=accepted_support,
            status=SupportTherapist.Status.ACCEPTED,
        )
        SupportTherapist.objects.create(
            therapist=self.therapist,
            support=pending_support,
            status=SupportTherapist.Status.PENDING,
        )
        alert = self._create_alert(timezone.now() - timezone.timedelta(hours=25))

        escalate_pending_alerts()

        alert.refresh_from_db()
        self.assertEqual(alert.escalation_level, 3)
        recipients = {recipient for message in mail.outbox for recipient in message.to}
        self.assertEqual(
            recipients,
            {self.therapist.email, accepted_support.email},
        )
        self.assertTrue(
            all("Escalat alt" in message.subject for message in mail.outbox)
        )

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_escalation_does_not_resend_email_when_level_is_unchanged(self):
        alert = self._create_alert(
            timezone.now() - timezone.timedelta(hours=25),
            escalation_level=3,
        )

        escalate_pending_alerts()

        alert.refresh_from_db()
        self.assertEqual(alert.escalation_level, 3)
        self.assertEqual(len(mail.outbox), 0)
