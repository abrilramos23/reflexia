from django.contrib import admin

from apps.analysis.models import EmotionalAnalysis


@admin.register(EmotionalAnalysis)
class EmotionalAnalysisAdmin(admin.ModelAdmin):
    list_display = ("entry", "primary_emotion", "risk_level", "analyzed_at", "reviewed_by_therapist")
    list_filter = ("risk_level", "reviewed_by_therapist", "analyzed_at")
    search_fields = ("entry__patient__email", "primary_emotion", "summary", "therapist_correction")
