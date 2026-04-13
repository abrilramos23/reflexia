from django.contrib import admin

from apps.entries.models import EmotionalAnalysis, JournalEntry, TherapistQuestion


@admin.register(TherapistQuestion)
class TherapistQuestionAdmin(admin.ModelAdmin):
    list_display = ("patient", "therapist", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("patient__email", "therapist__email", "question")


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ("patient", "status", "updated_at", "last_analyzed_at", "deleted_at")
    list_filter = ("status",)
    search_fields = ("patient__email", "content")


@admin.register(EmotionalAnalysis)
class EmotionalAnalysisAdmin(admin.ModelAdmin):
    list_display = ("entry", "primary_emotion", "tone", "updated_at")
    search_fields = ("entry__patient__email", "summary", "anonymized_content")
