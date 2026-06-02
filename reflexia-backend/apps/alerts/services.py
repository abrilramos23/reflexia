from django.conf import settings
from django.core.mail import send_mail

from apps.alerts.models import Alert, AlertNotification
from apps.entries.models import JournalEntry
import logging

logger = logging.getLogger(__name__)


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


def send_reminder_email(patient, days, last_entry_date):
    context = {
        'first_name': patient.first_name,
        'days': days,
        'last_entry_date': last_entry_date.strftime('%d/%m/%Y'),
        'app_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:5173'),
    }

    subject = f"Com estàs, {patient.first_name}?"
    message = (
        f"Hola {patient.first_name},\n\n"
        f"Notem que fa {days} dies que no escrius cap entrada al teu diari emocional a Reflexia.\n"
        f"L'última vegada que vas escriure va ser el {last_entry_date.strftime('%d/%m/%Y')}.\n\n"
        f"Si necessites suport o simplement vols compartir com et sents, recorda que el teu diari és un espai segur per expressar-te.\n"
        f"Si tens dificultats, no dubtis a contactar amb el teu terapeuta o amb els teus contactes de suport.\n\n"
        f"---\n"
        f"Reflexia - Sistema de Suport Emocional"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[patient.email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error(
            f"Error enviant recordatori a {patient.email}: {e}"
        )

def notify_escalation_level(alert):
    pass