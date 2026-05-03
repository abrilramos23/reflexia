from django.utils import timezone
from rest_framework import serializers

from apps.analysis.models import EmotionalAnalysis


ANALYSIS_DISCLAIMER = (
    "Aquesta analisi es orientativa, no substitueix el criteri clinic i sera revisada pel terapeuta."
)


class EmotionScoreSerializer(serializers.Serializer):
    emotion = serializers.CharField()
    percentage = serializers.FloatField(min_value=0, max_value=100)


class EmotionalAnalysisSerializer(serializers.ModelSerializer):
    emotions = EmotionScoreSerializer(many=True)
    disclaimer = serializers.SerializerMethodField()
    corrected_by_name = serializers.SerializerMethodField()

    class Meta:
        model = EmotionalAnalysis
        fields = (
            "id",
            "emotions",
            "primary_emotion",
            "risk_level",
            "summary",
            "tone",
            "key_themes",
            "recommendations",
            "therapist_correction",
            "corrected_by",
            "corrected_by_name",
            "corrected_at",
            "created_at",
            "updated_at",
            "disclaimer",
        )
        read_only_fields = fields

    def get_disclaimer(self, obj):
        return ANALYSIS_DISCLAIMER

    def get_corrected_by_name(self, obj):
        if not obj.corrected_by:
            return ""
        return f"{obj.corrected_by.first_name} {obj.corrected_by.last_name}".strip()


class AnalysisCorrectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmotionalAnalysis
        fields = ("therapist_correction",)

    def validate_therapist_correction(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("La correccio no pot estar buida.")
        return value.strip()

    def validate(self, attrs):
        if not attrs.get("therapist_correction"):
            raise serializers.ValidationError({"therapist_correction": "La correccio no pot estar buida."})
        return attrs

    def update(self, instance, validated_data):
        instance.therapist_correction = validated_data["therapist_correction"]
        instance.corrected_by = self.context["therapist"]
        instance.corrected_at = timezone.now()
        instance.save(update_fields=["therapist_correction", "corrected_by", "corrected_at", "updated_at"])
        return instance
