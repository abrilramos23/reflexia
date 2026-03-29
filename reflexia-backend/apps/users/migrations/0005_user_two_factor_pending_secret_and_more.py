from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_professionaldirectoryentry_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="two_factor_pending_secret",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="user",
            name="two_factor_secret",
            field=models.CharField(blank=True, max_length=64),
        ),
    ]
