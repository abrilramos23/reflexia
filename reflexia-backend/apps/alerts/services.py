from django.conf import settings
from django.core.mail import send_mail

from apps.alerts.models import Alert, AlertNotification


def send_alert_email_to_contact(alert, contact):
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
    # This is a placeholder for future escalation logic
    pass
