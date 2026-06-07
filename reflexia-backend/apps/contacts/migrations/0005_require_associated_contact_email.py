from django.db import migrations, models


def fill_missing_contact_emails(apps, schema_editor):
    AssociatedContact = apps.get_model("contacts", "AssociatedContact")
    contacts_without_email = AssociatedContact.objects.filter(
        models.Q(email__isnull=True) | models.Q(email="")
    )

    for contact in contacts_without_email:
        contact.email = f"contacte-{contact.pk}@example.invalid"
        contact.save(update_fields=["email"])


class Migration(migrations.Migration):

    dependencies = [
        ("contacts", "0004_supporttherapist_request_status"),
    ]

    operations = [
        migrations.RunPython(fill_missing_contact_emails, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name="associatedcontact",
            name="associated_contact_requires_email_or_phone",
        ),
        migrations.AlterField(
            model_name="associatedcontact",
            name="email",
            field=models.EmailField(max_length=255),
        ),
        migrations.AddConstraint(
            model_name="associatedcontact",
            constraint=models.CheckConstraint(
                check=~models.Q(email=""),
                name="associated_contact_requires_email",
            ),
        ),
    ]
