from rest_framework import serializers

from apps.analysis.models import EmotionalAnalysis


ANALYSIS_DISCLAIMER = (
    "Aquesta anàlisi és orientativa, no substitueix el criteri clínic i serà revisada pel terapeuta."
)


class EmotionScoreSerializer(serializers.Serializer):
    emotion = serializers.CharField()
    percentage = serializers.FloatField(min_value=0, max_value=100)


class EmotionalAnalysisSerializer(serializers.ModelSerializer):
    entry_id = serializers.UUIDField(read_only=True)
    emotions = EmotionScoreSerializer(many=True)
    disclaimer = serializers.SerializerMethodField()
    percentages = serializers.SerializerMethodField()
    analysis_date = serializers.DateTimeField(source="analyzed_at", read_only=True)
    reviewed = serializers.BooleanField(source="reviewed_by_therapist", read_only=True)
    manual_corrections = serializers.SerializerMethodField()

    class Meta:
        model = EmotionalAnalysis
        fields = (
            "entry_id",
            "emotions",
            "percentages",
            "primary_emotion",
            "risk_level",
            "summary",
            "recommendations",
            "analysis_date",
            "analyzed_at",
            "reviewed",
            "reviewed_by_therapist",
            "manual_corrections",
            "therapist_correction",
            "disclaimer",
        )
        read_only_fields = fields

    def get_disclaimer(self, obj):
        return ANALYSIS_DISCLAIMER

    def get_percentages(self, obj):
        return {item["emotion"]: item["percentage"] for item in obj.emotions}

    def get_manual_corrections(self, obj):
        if not obj.therapist_correction:
            return None
        return {
            "therapist_correction": obj.therapist_correction,
        }


class AnalysisCorrectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmotionalAnalysis
        fields = ("therapist_correction",)

    def validate_therapist_correction(self, value):
        return value.strip() if value else ""

    def update(self, instance, validated_data):
        instance.therapist_correction = validated_data.get("therapist_correction", "")
        instance.reviewed_by_therapist = True
        instance.save(update_fields=["therapist_correction", "reviewed_by_therapist"])
        return instance
