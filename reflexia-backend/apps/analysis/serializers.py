from rest_framework import serializers

from apps.analysis.models import EmotionalAnalysis


ANALYSIS_DISCLAIMER = (
    "Aquesta analisi es orientativa, no substitueix el criteri clinic i sera revisada pel terapeuta."
)


class EmotionScoreSerializer(serializers.Serializer):
    emotion = serializers.CharField()
    percentage = serializers.FloatField(min_value=0, max_value=100)


class EmotionalAnalysisSerializer(serializers.ModelSerializer):
    entry_id = serializers.UUIDField(read_only=True)
    emotions = EmotionScoreSerializer(many=True)
    disclaimer = serializers.SerializerMethodField()

    class Meta:
        model = EmotionalAnalysis
        fields = (
            "entry_id",
            "emotions",
            "primary_emotion",
            "risk_level",
            "summary",
            "recommendations",
            "analyzed_at",
            "reviewed_by_therapist",
            "therapist_correction",
            "disclaimer",
        )
        read_only_fields = fields

    def get_disclaimer(self, obj):
        return ANALYSIS_DISCLAIMER


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
        instance.reviewed_by_therapist = True
        instance.save(update_fields=["therapist_correction", "reviewed_by_therapist"])
        return instance
