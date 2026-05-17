from datetime import timedelta

from django.utils.html import strip_tags
from rest_framework import serializers
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field

from apps.analysis.serializers import EmotionalAnalysisSerializer
from apps.entries.models import JournalEntry, PrivateNote, TherapistQuestion


class TherapistQuestionSerializer(serializers.ModelSerializer):
    text = serializers.CharField(source="question", read_only=True)
    creation_date = serializers.DateTimeField(source="created_at", read_only=True)
    patient_name = serializers.SerializerMethodField()
    patient_id = serializers.UUIDField(source="patient.id", read_only=True)
    resolved = serializers.SerializerMethodField()

    class Meta:
        model = TherapistQuestion
        fields = (
            "id",
            "text",
            "question",
            "creation_date",
            "created_at",
            "resolved",
            "is_active",
            "patient_name",
            "patient_id",
        )
        read_only_fields = fields

    @extend_schema_field(OpenApiTypes.STR)
    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_resolved(self, obj):
        return not obj.is_active


class TherapistQuestionCreateSerializer(serializers.ModelSerializer):
    text = serializers.CharField(source="question")

    class Meta:
        model = TherapistQuestion
        fields = ("id", "text")
        read_only_fields = ("id",)

    def validate_text(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("La pregunta no pot estar buida.")
        return value.strip()


class PrivateNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivateNote
        fields = ("id", "content", "creation_date")
        read_only_fields = ("id", "creation_date")


class PrivateNoteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivateNote
        fields = ("id", "content")
        read_only_fields = ("id",)

    def validate_content(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("La nota privada no pot estar buida.")
        return value.strip()


class JournalEntrySerializer(serializers.ModelSerializer):
    therapist_question = TherapistQuestionSerializer(read_only=True)
    question = TherapistQuestionSerializer(source="therapist_question", read_only=True)
    analysis = EmotionalAnalysisSerializer(read_only=True)
    is_deleted = serializers.SerializerMethodField()
    preview = serializers.SerializerMethodField()
    creation_date = serializers.DateTimeField(source="created_at", read_only=True)
    modification_date = serializers.SerializerMethodField()

    class Meta:
        model = JournalEntry
        fields = (
            "id",
            "content",
            "preview",
            "status",
            "creation_date",
            "created_at",
            "modification_date",
            "updated_at",
            "retention_date",
            "is_deleted",
            "question",
            "therapist_question",
            "analysis",
        )
        read_only_fields = fields

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_deleted(self, obj):
        return obj.is_deleted

    @extend_schema_field(OpenApiTypes.STR)
    def get_preview(self, obj):
        plain_text = strip_tags(obj.content or "").strip()
        if len(plain_text) <= 120:
            return plain_text
        return f"{plain_text[:120]}..."

    @extend_schema_field(OpenApiTypes.DATETIME)
    def get_modification_date(self, obj):
        if not obj.updated_at or not obj.created_at:
            return None
        if (obj.updated_at - obj.created_at) <= timedelta(seconds=1):
            return None
        return obj.updated_at


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
        question = self._resolve_question(patient=patient, therapist_question_id=therapist_question_id)
        entry = JournalEntry.objects.create(
            patient=patient,
            therapist_question=question,
            status=JournalEntry.STATUS_ACTIVE,
            **validated_data,
        )
        self._resolve_question_if_needed(question)
        return entry

    def update(self, instance, validated_data):
        if instance.is_deleted:
            raise serializers.ValidationError({"detail": "No es poden editar les entrades eliminades."})

        therapist_question_id = validated_data.pop("therapist_question_id", serializers.empty)
        next_content = validated_data.get("content", instance.content)

        if therapist_question_id is not serializers.empty:
            instance.therapist_question = self._resolve_question(
                patient=self.context["patient"],
                therapist_question_id=therapist_question_id,
            )

        content_changed = next_content != instance.content
        question_changed = therapist_question_id is not serializers.empty
        instance.content = next_content
        if content_changed or question_changed:
            instance.status = JournalEntry.STATUS_MODIFIED

        instance.save(update_fields=["content", "status", "therapist_question", "updated_at"])
        self._resolve_question_if_needed(instance.therapist_question)

        if content_changed and hasattr(instance, "analysis"):
            instance.analysis.delete()

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

    def _resolve_question_if_needed(self, question):
        if question and question.is_active:
            question.is_active = False
            question.save(update_fields=["is_active", "updated_at"])

    def _has_meaningful_content(self, value):
        return bool(value and strip_tags(value).strip())
