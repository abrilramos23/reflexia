from django.utils import timezone
from django.utils.html import strip_tags
from rest_framework import serializers

from apps.analysis.services import build_emotional_analysis, anonymize_entry_content
from apps.entries.models import EmotionalAnalysis, JournalEntry, TherapistQuestion


class TherapistQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TherapistQuestion
        fields = ("id", "question", "created_at")


class EmotionalAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmotionalAnalysis
        fields = (
            "summary",
            "primary_emotion",
            "tone",
            "disclaimer",
            "created_at",
            "updated_at",
        )


class JournalEntrySerializer(serializers.ModelSerializer):
    analysis = EmotionalAnalysisSerializer(read_only=True)
    therapist_question = TherapistQuestionSerializer(read_only=True)
    is_deleted = serializers.SerializerMethodField()
    preview = serializers.SerializerMethodField()

    class Meta:
        model = JournalEntry
        fields = (
            "id",
            "content",
            "preview",
            "status",
            "created_at",
            "updated_at",
            "last_analyzed_at",
            "is_deleted",
            "therapist_question",
            "analysis",
        )
        read_only_fields = (
            "id",
            "status",
            "created_at",
            "updated_at",
            "last_analyzed_at",
            "is_deleted",
            "therapist_question",
            "analysis",
        )

    def get_is_deleted(self, obj):
        return obj.deleted_at is not None

    def get_preview(self, obj):
        plain_text = strip_tags(obj.content or "").strip()
        if len(plain_text) <= 120:
            return plain_text
        return f"{plain_text[:120]}..."


class JournalEntryDraftSerializer(serializers.ModelSerializer):
    therapist_question_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = JournalEntry
        fields = ("id", "content", "therapist_question_id")
        read_only_fields = ("id",)

    def validate_content(self, value):
        if not self._has_meaningful_content(value):
            raise serializers.ValidationError("L’entrada no pot estar buida.")
        return value.strip()

    def validate_therapist_question_id(self, value):
        patient = self.context["patient"]
        if value is None:
            return value

        try:
            question = TherapistQuestion.objects.get(pk=value, patient=patient)
        except TherapistQuestion.DoesNotExist as exc:
            raise serializers.ValidationError("La pregunta activa indicada no existeix.") from exc

        return question.pk

    def create(self, validated_data):
        patient = self.context["patient"]
        therapist_question_id = validated_data.pop("therapist_question_id", None)
        entry = JournalEntry.objects.create(
            patient=patient,
            therapist_question=self._resolve_question(patient=patient, therapist_question_id=therapist_question_id),
            **validated_data,
        )
        return entry

    def update(self, instance, validated_data):
        if instance.deleted_at is not None:
            raise serializers.ValidationError({"detail": "No es poden editar les entrades eliminades."})

        therapist_question_id = validated_data.pop("therapist_question_id", serializers.empty)
        next_content = validated_data.get("content", instance.content)
        content_changed = next_content != instance.content

        if therapist_question_id is not serializers.empty:
            instance.therapist_question = self._resolve_question(
                patient=self.context["patient"],
                therapist_question_id=therapist_question_id,
            )

        instance.content = next_content
        instance.status = JournalEntry.STATUS_DRAFT
        if content_changed:
            instance.last_analyzed_at = None

        instance.save(update_fields=["content", "status", "therapist_question", "last_analyzed_at", "updated_at"])

        if content_changed:
            EmotionalAnalysis.objects.filter(entry=instance).delete()

        return instance

    def _resolve_question(self, *, patient, therapist_question_id):
        if therapist_question_id:
            return TherapistQuestion.objects.get(pk=therapist_question_id, patient=patient)

        if self.instance and self.instance.therapist_question_id:
            return self.instance.therapist_question

        return (
            TherapistQuestion.objects.filter(patient=patient, is_active=True)
            .select_related("therapist", "patient")
            .first()
        )

    def _has_meaningful_content(self, value):
        return bool(value and strip_tags(value).strip())


class JournalEntryAnalyzeSerializer(serializers.Serializer):
    content = serializers.CharField(required=False, allow_blank=False)

    def validate_content(self, value):
        if not value or not strip_tags(value).strip():
            raise serializers.ValidationError("L’entrada no pot estar buida.")
        return value.strip()

    def save(self, **kwargs):
        entry = self.context["entry"]
        patient = self.context["patient"]

        if entry.deleted_at is not None:
            raise serializers.ValidationError({"detail": "No es poden editar les entrades eliminades."})

        content = self.validated_data.get("content")
        if content is not None:
            entry.content = content

        if not entry.content or not strip_tags(entry.content).strip():
            raise serializers.ValidationError({"content": "L’entrada no pot estar buida."})

        linked_question = entry.therapist_question
        therapist = linked_question.therapist if linked_question else None
        anonymized_content = anonymize_entry_content(
            content=entry.content,
            patient=patient,
            therapist=therapist,
        )
        analysis_payload = build_emotional_analysis(anonymized_content=anonymized_content)

        analysis, _ = EmotionalAnalysis.objects.update_or_create(
            entry=entry,
            defaults={
                "anonymized_content": anonymized_content,
                "summary": analysis_payload["summary"],
                "primary_emotion": analysis_payload["primary_emotion"],
                "tone": analysis_payload["tone"],
                "disclaimer": analysis_payload["disclaimer"],
            },
        )

        entry.status = JournalEntry.STATUS_ANALYZED
        entry.last_analyzed_at = timezone.now()
        entry.save(update_fields=["content", "status", "last_analyzed_at", "updated_at"])

        return entry, analysis
