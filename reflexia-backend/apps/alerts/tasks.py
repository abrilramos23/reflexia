from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from apps.alerts.models import Alert, AlertNotification
from apps.alerts.services import (
    notify_escalation_level,
    send_alert_email_to_contact,
    send_reminder_email,
)
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_inactivity_reminders():
    from apps.entries.models import JournalEntry
    from apps.users.models import Patient

    days = 3
    threshold = timezone.now() - timedelta(days=days)

    active_patients = Patient.objects.filter(
        is_active=True,
        legal_terms_accepted=True,
    )

    reminders_sent = 0

    for patient in active_patients:
        has_any_entry = JournalEntry.objects.filter(
            patient=patient,
        ).exclude(
            status=JournalEntry.STATUS_DELETED,
        ).exists()

        if not has_any_entry:
            continue

        last_entry = JournalEntry.objects.filter(
            patient=patient,
        ).exclude(
            status=JournalEntry.STATUS_DELETED,
        ).order_by('-created_at').first()

        if last_entry and last_entry.created_at < threshold:
            send_reminder_email(patient, days, last_entry.created_at)
            reminders_sent += 1

    logger.info(f"Recordatoris d'inactivitat enviats: {reminders_sent}")
    return reminders_sent

@shared_task(bind=True, max_retries=3)
def send_alert_to_contact_task(self, alert_id, contact_id):
    try:
        alert = Alert.objects.get(id=alert_id)
        from apps.contacts.models import AssociatedContact
        contact = AssociatedContact.objects.get(id=contact_id)

        send_alert_email_to_contact(alert, contact)

        AlertNotification.objects.create(
            alert=alert,
            contact=contact,
            status=AlertNotification.Status.SENT,
            recipient_email=contact.email,
            method=AlertNotification.Method.EMAIL,
        )

        return f"Alert sent successfully to {contact.email}"

    except ObjectDoesNotExist as exc:
        raise exc

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def escalate_pending_alerts():
    now = timezone.now()
    pending_alerts = Alert.objects.filter(status=Alert.Status.PENDING)

    for alert in pending_alerts:
        target_level = _target_escalation_level(alert, now)
        if target_level <= alert.escalation_level:
            continue

        alert.escalation_level = target_level
        alert.last_escalation_at = now
        alert.save(update_fields=['escalation_level', 'last_escalation_at'])
        notify_escalation_level(alert)


def _target_escalation_level(alert, now):
    age = now - alert.created_at

    if age >= timedelta(hours=24):
        return 3

    if age >= timedelta(hours=4):
        return 2

    if age >= timedelta(hours=1):
        return 1

    return 0


@shared_task
def batch_send_alerts_to_contacts(alert_id, contact_ids):
    from apps.contacts.models import AssociatedContact

    try:
        alert = Alert.objects.get(id=alert_id)
        contacts = AssociatedContact.objects.filter(id__in=contact_ids)

        for contact in contacts:
            send_alert_to_contact_task.delay(alert_id, contact.id)

        return f"Batch task enqueued: {len(contacts)} contacts"

    except ObjectDoesNotExist:
        return f"Alert {alert_id} not found"
