from celery import shared_task
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from apps.alerts.models import Alert, AlertNotification
from apps.alerts.services import send_alert_email_to_contact


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
    from datetime import timedelta
    now = timezone.now()

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
