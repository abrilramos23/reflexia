from django.utils.html import strip_tags
from rest_framework import serializers

from apps.entries.models import JournalEntry, TherapistQuestion


class TherapistQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TherapistQuestion
        fields = ("id", "question", "created_at")


class JournalEntrySerializer(serializers.ModelSerializer):
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
            "is_deleted",
            "therapist_question",
        )
        read_only_fields = (
            "id",
            "status",
            "created_at",
            "updated_at",
            "is_deleted",
            "therapist_question",
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

        if therapist_question_id is not serializers.empty:
            instance.therapist_question = self._resolve_question(
                patient=self.context["patient"],
                therapist_question_id=therapist_question_id,
            )

        instance.content = next_content
        instance.status = JournalEntry.STATUS_DRAFT

        instance.save(update_fields=["content", "status", "therapist_question", "updated_at"])

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
