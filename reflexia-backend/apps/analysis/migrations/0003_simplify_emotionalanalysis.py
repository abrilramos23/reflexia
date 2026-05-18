from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("analysis", "0002_alter_emotionalanalysis_risk_level"),
    ]

    operations = [
        migrations.RenameField(
            model_name="emotionalanalysis",
            old_name="created_at",
            new_name="analyzed_at",
        ),
        migrations.RemoveField(
            model_name="emotionalanalysis",
            name="corrected_by",
        ),
        migrations.RemoveField(
            model_name="emotionalanalysis",
            name="corrected_at",
        ),
        migrations.RemoveField(
            model_name="emotionalanalysis",
            name="id",
        ),
        migrations.RemoveField(
            model_name="emotionalanalysis",
            name="key_themes",
        ),
        migrations.RemoveField(
            model_name="emotionalanalysis",
            name="model_name",
        ),
        migrations.RemoveField(
            model_name="emotionalanalysis",
            name="model_response_id",
        ),
        migrations.RemoveField(
            model_name="emotionalanalysis",
            name="raw_response",
        ),
        migrations.RemoveField(
            model_name="emotionalanalysis",
            name="tone",
        ),
        migrations.RemoveField(
            model_name="emotionalanalysis",
            name="updated_at",
        ),
        migrations.AddField(
            model_name="emotionalanalysis",
            name="reviewed_by_therapist",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="emotionalanalysis",
            name="analyzed_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name="emotionalanalysis",
            name="entry",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                primary_key=True,
                related_name="analysis",
                serialize=False,
                to="entries.journalentry",
            ),
        ),
        migrations.AlterModelOptions(
            name="emotionalanalysis",
            options={
                "ordering": ("-analyzed_at",),
                "verbose_name": "emotional analysis",
                "verbose_name_plural": "emotional analyses",
            },
        ),
    ]
