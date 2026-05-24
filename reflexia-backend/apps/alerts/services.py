from django.conf import settings
from django.core.mail import send_mail

from apps.alerts.models import Alert, AlertNotification


def send_alert_email_to_contact(alert, contact):
    """
    Send alert notification to associated contact.
    RGPD: Only send patient first name + risk level, NOT full content.

    Args:
        alert: Alert instance
        contact: AssociatedContact instance

    Raises:
        Exception: If email sending fails
    """
    subject = f"Alerta de suport emocional per a {alert.patient.first_name}"

    message = (
        f"Hola {contact.name},\n\n"
        f"Hem detectat un nivell de risc elevat en l'entrada emocional de "
        f"{alert.patient.first_name}.\n\n"
        f"El seu terapeuta ha validat aquesta alerta i et contacta com a contacte de suport.\n"
        f"Si disposes de temps, considera posar-te en contacte amb {alert.patient.first_name} "
        f"per oferir suport emocional.\n\n"
        f"Aquesta és una notificació automàtica. Si teniu preguntes, contacteu directament "
        f"amb {alert.patient.first_name} o amb el seu terapeuta.\n\n"
        f"---\n"
        f"Reflexia - Sistema de Suport Emocional"
    )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [contact.email],
        fail_silently=False,
    )


def notify_escalation_level(alert):
    """
    Escalate alert notification if not responded.
    Called by celery task or management command periodically.

    Levels:
    - 0: Created (initial state)
    - 1: 1 hour passed - re-notify support therapist
    - 2: 4 hours passed - notify clinic admin
    - 3: 24 hours passed - critical, notify supervisor

    Args:
        alert: Alert instance
    """
    # This is a placeholder for future escalation logic
    # When implemented, should:
    # 1. Check time elapsed since creation
    # 2. Determine escalation level
    # 3. Send notifications to support therapist / admin
    pass
