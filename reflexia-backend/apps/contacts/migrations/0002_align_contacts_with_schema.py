from django.db import migrations, models
import django.db.models.deletion


def migrate_patient_contact_links(apps, schema_editor):
    AssociatedContact = apps.get_model("contacts", "AssociatedContact")
    DefaultContact = apps.get_model("contacts", "DefaultContact")

    for contact in AssociatedContact.objects.all().iterator():
        DefaultContact.objects.update_or_create(
            patient_id=contact.patient_id,
            contact_id=contact.id,
            defaults={"is_default": contact.is_default},
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("contacts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DefaultContact",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_default", models.BooleanField(default=False)),
                (
                    "contact",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="patient_links", to="contacts.associatedcontact"),
                ),
                (
                    "patient",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="default_contact_links", to="users.patient"),
                ),
            ],
            options={
                "verbose_name": "patient-associated contact relationship",
                "verbose_name_plural": "patient-associated contact relationships",
            },
        ),
        migrations.RunPython(migrate_patient_contact_links, noop_reverse),
        migrations.RenameField(
            model_name="associatedcontact",
            old_name="relationship",
            new_name="relation",
        ),
        migrations.RemoveField(
            model_name="associatedcontact",
            name="created_at",
        ),
        migrations.RemoveField(
            model_name="associatedcontact",
            name="is_default",
        ),
        migrations.RemoveField(
            model_name="associatedcontact",
            name="patient",
        ),
        migrations.RemoveField(
            model_name="associatedcontact",
            name="updated_at",
        ),
        migrations.AlterField(
            model_name="associatedcontact",
            name="email",
            field=models.EmailField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="associatedcontact",
            name="name",
            field=models.CharField(max_length=150),
        ),
        migrations.AlterField(
            model_name="associatedcontact",
            name="phone",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name="associatedcontact",
            name="relation",
            field=models.CharField(max_length=100),
        ),
        migrations.AddConstraint(
            model_name="associatedcontact",
            constraint=models.CheckConstraint(
                check=(
                    (models.Q(email__isnull=False) & ~models.Q(email=""))
                    | (models.Q(phone__isnull=False) & ~models.Q(phone=""))
                ),
                name="associated_contact_requires_email_or_phone",
            ),
        ),
        migrations.AddConstraint(
            model_name="defaultcontact",
            constraint=models.UniqueConstraint(fields=("patient", "contact"), name="unique_patient_contact_relationship"),
        ),
        migrations.RemoveConstraint(
            model_name="supporttherapist",
            name="unique_support_therapist_relationship",
        ),
        migrations.RenameField(
            model_name="supporttherapist",
            old_name="support_therapist",
            new_name="support",
        ),
        migrations.RemoveField(
            model_name="supporttherapist",
            name="created_at",
        ),
        migrations.AddConstraint(
            model_name="supporttherapist",
            constraint=models.UniqueConstraint(fields=("therapist", "support"), name="unique_support_therapist_relationship"),
        ),
        migrations.AddConstraint(
            model_name="supporttherapist",
            constraint=models.CheckConstraint(
                check=~models.Q(therapist=models.F("support")),
                name="support_therapist_cannot_match_therapist",
            ),
        ),
    ]
