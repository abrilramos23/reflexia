from django.conf import settings
from django.core.mail import send_mail

from apps.alerts.models import Alert, AlertNotification
from apps.contacts.models import SupportTherapist
from apps.entries.models import JournalEntry
import logging

logger = logging.getLogger(__name__)

HIGH_ESCALATION_LEVEL = 3


def send_alert_email_to_contact(alert, contact):
    subject = f"Alerta de suport emocional per a {alert.patient.first_name}"
    justification = alert.justification.strip() or "No especificada."

    message = (
        f"Hola {contact.name},\n\n"
        f"Hem detectat un nivell de risc elevat en l'entrada emocional de "
        f"{alert.patient.first_name}.\n\n"
        f"El seu terapeuta ha validat aquesta alerta i et contacta com a contacte de suport.\n"
        f"Justificació de la notificació: {justification}\n\n"
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
    therapists = _active_alert_therapists(alert)
    if not therapists:
        return 0

    recipients = _unique_therapist_recipients(therapists)

    if alert.escalation_level >= HIGH_ESCALATION_LEVEL:
        support_therapists = _accepted_support_therapists(therapists)
        recipients.extend(_unique_therapist_recipients(support_therapists, existing=recipients))

    sent_count = 0
    for therapist in recipients:
        try:
            send_escalation_email_to_therapist(alert, therapist)
            sent_count += 1
        except Exception as exc:
            logger.error(
                "Error enviant escalat d'alerta %s a %s: %s",
                alert.pk,
                therapist.email,
                exc,
            )

    return sent_count


def send_escalation_email_to_therapist(alert, therapist):
    subject = _escalation_subject(alert)
    message = _escalation_message(alert, therapist)

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [therapist.email],
        fail_silently=False,
    )


def _active_alert_therapists(alert):
    return [
        link.therapist
        for link in alert.patient.therapist_links.filter(is_active=True).select_related("therapist")
        if link.therapist.email
    ]


def _accepted_support_therapists(therapists):
    return [
        link.support
        for link in SupportTherapist.objects.filter(
            therapist__in=therapists,
            status=SupportTherapist.Status.ACCEPTED,
        ).select_related("support")
        if link.support.email
    ]


def _unique_therapist_recipients(therapists, existing=None):
    seen = {therapist.email.lower() for therapist in existing or [] if therapist.email}
    recipients = []

    for therapist in therapists:
        email = therapist.email.lower()
        if email in seen:
            continue
        seen.add(email)
        recipients.append(therapist)

    return recipients


def _escalation_subject(alert):
    if alert.escalation_level >= HIGH_ESCALATION_LEVEL:
        return "Escalat alt d'una alerta clínica a Reflexia"

    return f"Escalat de nivell {alert.escalation_level} d'una alerta clínica a Reflexia"


def _escalation_message(alert, therapist):
    patient = alert.patient
    alert_url = f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')}/alerts/{alert.pk}"

    return (
        f"Hola {therapist.first_name},\n\n"
        f"L'alerta clínica de {patient.first_name} {patient.last_name} "
        f"ha escalat al nivell {alert.escalation_level} perquè continua pendent de revisió.\n\n"
        f"Nivell de risc: {alert.get_risk_level_display()}\n"
        f"Data de creació de l'alerta: {alert.created_at.strftime('%d/%m/%Y %H:%M')}\n\n"
        f"Pots revisar-la aquí:\n{alert_url}\n\n"
        "Aquest missatge és automàtic i no substitueix el criteri professional."
    )
