from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def populate_private_note_patients(apps, schema_editor):
    PrivateNote = apps.get_model("entries", "PrivateNote")

    for note in PrivateNote.objects.select_related("entry").filter(patient__isnull=True):
        note.patient_id = note.entry.patient_id
        note.save(update_fields=["patient"])


class Migration(migrations.Migration):

    dependencies = [
        ("entries", "0005_private_notes_retention_and_statuses"),
    ]

    operations = [
        migrations.AddField(
            model_name="privatenote",
            name="patient",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="private_notes",
                to="users.patient",
            ),
        ),
        migrations.AddField(
            model_name="privatenote",
            name="updated_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.RunPython(populate_private_note_patients, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="privatenote",
            name="patient",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="private_notes",
                to="users.patient",
            ),
        ),
        migrations.AlterField(
            model_name="privatenote",
            name="therapist",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="private_patient_notes",
                to="users.therapist",
            ),
        ),
        migrations.AlterField(
            model_name="privatenote",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.RemoveField(
            model_name="privatenote",
            name="entry",
        ),
    ]
