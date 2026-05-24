from celery import shared_task
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from apps.alerts.models import Alert, AlertNotification
from apps.alerts.services import send_alert_email_to_contact


@shared_task(bind=True, max_retries=3)
def send_alert_to_contact_task(self, alert_id, contact_id):
    """
    Asincrónic task to send alert notification to a contact.

    Args:
        alert_id: Alert UUID
        contact_id: AssociatedContact UUID
    """
    try:
        alert = Alert.objects.get(id=alert_id)
        from apps.contacts.models import AssociatedContact
        contact = AssociatedContact.objects.get(id=contact_id)

        send_alert_email_to_contact(alert, contact)

        # Create notification record
        AlertNotification.objects.create(
            alert=alert,
            contact=contact,
            status=AlertNotification.Status.SENT,
            recipient_email=contact.email,
            method=AlertNotification.Method.EMAIL,
        )

        return f"Alert sent successfully to {contact.email}"

    except ObjectDoesNotExist as exc:
        # Don't retry if object doesn't exist
        raise exc

    except Exception as exc:
        # Retry up to 3 times with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def escalate_pending_alerts():
    """
    Periodic task to escalate alerts that haven't been handled.
    Runs every 30 minutes (configured in celery.py beat schedule).

    Escalation levels:
    - Level 0: Created (initial state, no action)
    - Level 1: 1 hour passed - notify support therapist
    - Level 2: 4 hours passed - notify clinic admin
    - Level 3: 24 hours passed - critical, notify director
    """
    from datetime import timedelta
    now = timezone.now()

    # Level 1: 1 hour since creation
    one_hour_ago = now - timedelta(hours=1)
    alerts_level_0 = Alert.objects.filter(
        status=Alert.Status.PENDING,
        escalation_level=0,
        created_at__lt=one_hour_ago,
    )

    for alert in alerts_level_0:
        alert.escalation_level = 1
        alert.last_escalation_at = now
        alert.save(update_fields=['escalation_level', 'last_escalation_at'])
        # Could send notification to support therapist here

    # Level 2: 4 hours since creation
    four_hours_ago = now - timedelta(hours=4)
    alerts_level_1 = Alert.objects.filter(
        status=Alert.Status.PENDING,
        escalation_level__lt=2,
        created_at__lt=four_hours_ago,
    )

    for alert in alerts_level_1:
        alert.escalation_level = 2
        alert.last_escalation_at = now
        alert.save(update_fields=['escalation_level', 'last_escalation_at'])
        # Could send notification to clinic admin here

    # Level 3: 24 hours since creation
    one_day_ago = now - timedelta(hours=24)
    alerts_level_2 = Alert.objects.filter(
        status=Alert.Status.PENDING,
        escalation_level__lt=3,
        created_at__lt=one_day_ago,
    )

    for alert in alerts_level_2:
        alert.escalation_level = 3
        alert.last_escalation_at = now
        alert.save(update_fields=['escalation_level', 'last_escalation_at'])
        # Could send critical notification here


@shared_task
def batch_send_alerts_to_contacts(alert_id, contact_ids):
    """
    Batch task to send alert to multiple contacts.

    Args:
        alert_id: Alert UUID
        contact_ids: List of AssociatedContact UUIDs
    """
    from apps.contacts.models import AssociatedContact

    try:
        alert = Alert.objects.get(id=alert_id)
        contacts = AssociatedContact.objects.filter(id__in=contact_ids)

        for contact in contacts:
            send_alert_to_contact_task.delay(alert_id, contact.id)

        return f"Batch task enqueued: {len(contacts)} contacts"

    except ObjectDoesNotExist:
        return f"Alert {alert_id} not found"
