from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("entries", "0002_remove_journalentry_last_analyzed_at_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="journalentry",
            name="status",
            field=models.CharField(
                choices=[("draft", "Draft"), ("analyzed", "Analyzed")],
                default="draft",
                max_length=20,
            ),
        ),
    ]
