from django.db import migrations, models


def move_platform_admins_to_therapists(apps, schema_editor):
    User = apps.get_model("users", "User")
    User.objects.filter(role="platform_admin").update(role="therapist")


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0011_invitacioorganitzacio_email"),
    ]

    operations = [
        migrations.RunPython(move_platform_admins_to_therapists, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("therapist", "Therapist"),
                    ("patient", "Patient"),
                ],
                default="patient",
                max_length=20,
            ),
        ),
    ]
