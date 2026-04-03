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
            name="AssociatedContact",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
                ("relationship", models.CharField(max_length=150)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("phone", models.CharField(blank=True, max_length=50)),
                ("is_default", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "patient",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="associated_contacts", to="users.patient"),
                ),
            ],
            options={
                "verbose_name": "associated contact",
                "verbose_name_plural": "associated contacts",
                "ordering": ("-is_default", "name"),
            },
        ),
        migrations.CreateModel(
            name="SupportTherapist",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "support_therapist",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="supported_by_links", to="users.therapist"),
                ),
                (
                    "therapist",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="support_therapist_links", to="users.therapist"),
                ),
            ],
            options={
                "verbose_name": "support therapist relationship",
                "verbose_name_plural": "support therapist relationships",
            },
        ),
        migrations.AddConstraint(
            model_name="supporttherapist",
            constraint=models.UniqueConstraint(fields=("therapist", "support_therapist"), name="unique_support_therapist_relationship"),
        ),
    ]
