from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0008_delete_subscription"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="organisationmember",
            constraint=models.UniqueConstraint(
                fields=("user",),
                name="unique_organisation_membership_per_user",
            ),
        ),
    ]
