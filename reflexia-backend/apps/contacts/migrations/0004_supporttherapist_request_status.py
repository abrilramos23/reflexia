from django.db import migrations, models
import django.utils.timezone


def mark_existing_support_as_accepted(apps, schema_editor):
    SupportTherapist = apps.get_model("contacts", "SupportTherapist")
    SupportTherapist.objects.update(status="accepted", responded_at=django.utils.timezone.now())


class Migration(migrations.Migration):

    dependencies = [
        ("contacts", "0003_alter_associatedcontact_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="supporttherapist",
            name="requested_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name="supporttherapist",
            name="responded_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="supporttherapist",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("accepted", "Accepted"),
                    ("rejected", "Rejected"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.RunPython(mark_existing_support_as_accepted, migrations.RunPython.noop),
        migrations.AlterModelOptions(
            name="supporttherapist",
            options={
                "ordering": ("-requested_at",),
                "verbose_name": "support therapist relationship",
                "verbose_name_plural": "support therapist relationships",
            },
        ),
    ]
