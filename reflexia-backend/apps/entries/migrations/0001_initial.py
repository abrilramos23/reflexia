from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("users", "0005_user_two_factor_pending_secret_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="TherapistQuestion",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("question", models.TextField()),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="active_journal_questions",
                        to="users.patient",
                    ),
                ),
                (
                    "therapist",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="journal_questions",
                        to="users.therapist",
                    ),
                ),
            ],
            options={
                "verbose_name": "therapist question",
                "verbose_name_plural": "therapist questions",
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="JournalEntry",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("content", models.TextField()),
                ("status", models.CharField(choices=[("draft", "Draft"), ("analyzed", "Analyzed")], default="draft", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("last_analyzed_at", models.DateTimeField(blank=True, null=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="journal_entries",
                        to="users.patient",
                    ),
                ),
                (
                    "therapist_question",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="entries",
                        to="entries.therapistquestion",
                    ),
                ),
            ],
            options={
                "verbose_name": "journal entry",
                "verbose_name_plural": "journal entries",
                "ordering": ("-updated_at",),
            },
        ),
        migrations.CreateModel(
            name="EmotionalAnalysis",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("anonymized_content", models.TextField()),
                ("summary", models.TextField()),
                ("primary_emotion", models.CharField(max_length=50)),
                ("tone", models.CharField(max_length=50)),
                ("disclaimer", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
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
            },
        ),
    ]
