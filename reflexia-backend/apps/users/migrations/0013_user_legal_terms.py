from django.db import migrations, models
import django.utils.timezone


def migrate_patient_consent_to_user(apps, schema_editor):
    Patient = apps.get_model("users", "Patient")
    User = apps.get_model("users", "User")
    for patient in Patient.objects.all().only("id", "consent_accepted", "consent_date"):
        if patient.consent_accepted:
            User.objects.filter(pk=patient.pk).update(
                legal_terms_accepted=True,
                legal_terms_accepted_at=patient.consent_date or django.utils.timezone.now(),
                legal_terms_version="2026-05-20",
            )


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0012_remove_platform_admin_role"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="legal_terms_accepted",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="legal_terms_accepted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="legal_terms_version",
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.RunPython(migrate_patient_consent_to_user, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="patient",
            name="consent_accepted",
        ),
        migrations.RemoveField(
            model_name="patient",
            name="consent_date",
        ),
    ]
