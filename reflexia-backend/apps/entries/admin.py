from django.contrib import admin

from apps.entries.models import JournalEntry, TherapistQuestion


@admin.register(TherapistQuestion)
class TherapistQuestionAdmin(admin.ModelAdmin):
    list_display = ("patient", "therapist", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("patient__email", "therapist__email", "question")


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ("patient", "status", "updated_at", "deleted_at")
    list_filter = ("status",)
    search_fields = ("patient__email", "content")
