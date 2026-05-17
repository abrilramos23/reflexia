from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("entries", "0003_journalentry_status_analyzed"),
    ]

    operations = [
        migrations.AlterField(
            model_name="journalentry",
            name="status",
            field=models.CharField(
                choices=[("draft", "Draft"), ("analyzed", "Analyzed"), ("deleted", "Deleted")],
                default="draft",
                max_length=20,
            ),
        ),
    ]
