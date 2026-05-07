from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid

import apps.entries.models


def migrate_entry_statuses(apps, schema_editor):
    JournalEntry = apps.get_model("entries", "JournalEntry")
    JournalEntry.objects.filter(status="draft").update(status="active")
    JournalEntry.objects.filter(status="analyzed").update(status="modified")


class Migration(migrations.Migration):

    dependencies = [
        ("entries", "0004_alter_journalentry_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="journalentry",
            name="retention_date",
            field=models.DateTimeField(default=apps.entries.models.default_entry_retention_date),
        ),
        migrations.AlterField(
            model_name="journalentry",
            name="status",
            field=models.CharField(
                choices=[("active", "Active"), ("modified", "Modified"), ("deleted", "Deleted")],
                default="active",
                max_length=20,
            ),
        ),
        migrations.RunPython(migrate_entry_statuses, migrations.RunPython.noop),
        migrations.CreateModel(
            name="PrivateNote",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("content", models.TextField()),
                ("creation_date", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "entry",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="private_notes",
                        to="entries.journalentry",
                    ),
                ),
                (
                    "therapist",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="private_entry_notes",
                        to="users.therapist",
                    ),
                ),
            ],
            options={
                "ordering": ("-creation_date",),
                "verbose_name": "private note",
                "verbose_name_plural": "private notes",
            },
        ),
    ]
