from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.analysis.models import EmotionalAnalysis
from apps.alerts.models import Alert


@receiver(post_save, sender=EmotionalAnalysis)
def create_alert_on_high_risk(sender, instance, created, **kwargs):
    if created and instance.risk_level == EmotionalAnalysis.HIGH:
        Alert.objects.get_or_create(
            emotional_analysis=instance,
            defaults={
                "patient": instance.entry.patient,
                "risk_level": instance.risk_level,
                "status": Alert.Status.PENDING,
            },
        )

