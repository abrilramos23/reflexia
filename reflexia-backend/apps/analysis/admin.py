from django.contrib import admin

from apps.analysis.models import EmotionalAnalysis


@admin.register(EmotionalAnalysis)
class EmotionalAnalysisAdmin(admin.ModelAdmin):
    list_display = ("entry", "primary_emotion", "risk_level", "updated_at", "corrected_by")
    list_filter = ("risk_level", "created_at", "updated_at")
    search_fields = ("entry__patient__email", "primary_emotion", "summary", "therapist_correction")
