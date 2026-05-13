import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("entries", "0002_remove_journalentry_last_analyzed_at_and_more"),
        ("users", "0009_limit_organisationmember_to_one_org_per_user"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmotionalAnalysis",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "emotions",
                    models.JSONField(default=list),
                ),
                ("primary_emotion", models.CharField(max_length=80)),
                (
                    "risk_level",
                    models.CharField(
                        choices=[
                            ("low", "Low"),
                            ("moderate", "Moderate"),
                            ("high", "High"),
                            ("crisis", "Crisis"),
                        ],
                        max_length=20,
                    ),
                ),
                ("summary", models.TextField()),
                ("tone", models.CharField(blank=True, max_length=120)),
                ("key_themes", models.JSONField(blank=True, default=list)),
                ("recommendations", models.JSONField(blank=True, default=list)),
                ("model_name", models.CharField(blank=True, max_length=120)),
                ("model_response_id", models.CharField(blank=True, max_length=120)),
                ("raw_response", models.JSONField(blank=True, default=dict)),
                ("therapist_correction", models.TextField(blank=True)),
                ("corrected_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "corrected_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="analysis_corrections",
                        to="users.therapist",
                    ),
                ),
                (
                    "entry",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="analysis",
                        to="entries.journalentry",
                    ),
                ),
            ],
            options={
                "verbose_name": "emotional analysis",
                "verbose_name_plural": "emotional analyses",
                "ordering": ("-updated_at",),
            },
        ),
    ]
