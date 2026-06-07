from datetime import datetime
from uuid import UUID

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.alerts.models import Alert, AlertNotification
from apps.analysis.models import EmotionalAnalysis
from apps.contacts.models import AssociatedContact
from apps.entries.models import JournalEntry
from apps.users.models import Patient


class AlertNotificationSerializer(serializers.ModelSerializer):
    contact_name = serializers.CharField(source="contact.name", read_only=True)
    contact_email = serializers.EmailField(source="contact.email", read_only=True)

    class Meta:
        model = AlertNotification
        fields = (
            "id",
            "contact_name",
            "contact_email",
            "sent_at",
            "method",
            "status",
            "error_message",
        )
        read_only_fields = fields


class AssociatedContactForAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssociatedContact
        fields = ("id", "name", "email", "phone", "relation")
        read_only_fields = fields


class AlertListSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    patient_id = serializers.UUIDField(source="patient.id", read_only=True)
    entry_date = serializers.SerializerMethodField()
    risk_label = serializers.CharField(source="get_risk_level_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Alert
        fields = (
            "id",
            "patient_id",
            "patient_name",
            "risk_level",
            "risk_label",
            "status",
            "status_label",
            "created_at",
            "escalation_level",
            "entry_date",
        )
        read_only_fields = fields

    def get_patient_name(self, obj) -> str:
        return f"{obj.patient.first_name} {obj.patient.last_name}"

    def get_entry_date(self, obj) -> datetime:
        return obj.emotional_analysis.entry.created_at


class AlertDetailSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    patient_id = serializers.UUIDField(source="patient.id", read_only=True)
    patient_email = serializers.EmailField(source="patient.email", read_only=True)
    entry_content = serializers.SerializerMethodField()
    entry_date = serializers.SerializerMethodField()
    entry_id = serializers.SerializerMethodField()
    analysis_summary = serializers.CharField(
        source="emotional_analysis.summary", read_only=True
    )
    analysis_emotions = serializers.JSONField(
        source="emotional_analysis.emotions", read_only=True
    )
    analysis_primary_emotion = serializers.CharField(
        source="emotional_analysis.primary_emotion", read_only=True
    )
    analysis_recommendations = serializers.JSONField(
        source="emotional_analysis.recommendations", read_only=True
    )
    associated_contacts = serializers.SerializerMethodField()
    validating_therapist_name = serializers.SerializerMethodField()
    risk_label = serializers.CharField(source="get_risk_level_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Alert
        fields = (
            "id",
            "patient_id",
            "patient_name",
            "patient_email",
            "entry_id",
            "entry_date",
            "entry_content",
            "risk_level",
            "risk_label",
            "status",
            "status_label",
            "analysis_summary",
            "analysis_emotions",
            "analysis_primary_emotion",
            "analysis_recommendations",
            "escalation_level",
            "created_at",
            "validated_at",
            "validation_note",
            "justification",
            "validating_therapist_name",
            "associated_contacts",
        )
        read_only_fields = fields

    def get_patient_name(self, obj) -> str:
        return f"{obj.patient.first_name} {obj.patient.last_name}"

    def get_entry_content(self, obj) -> str:
        entry = obj.emotional_analysis.entry
        content = entry.content
        return content[:500] + "..." if len(content) > 500 else content

    def get_entry_date(self, obj) -> datetime:
        return obj.emotional_analysis.entry.created_at

    def get_entry_id(self, obj) -> UUID:
        return obj.emotional_analysis.entry.id

    @extend_schema_field(AssociatedContactForAlertSerializer(many=True))
    def get_associated_contacts(self, obj):
        contacts = obj.patient.default_contact_links.select_related("contact")
        contact_list = [link.contact for link in contacts]
        return AssociatedContactForAlertSerializer(contact_list, many=True).data

    def get_validating_therapist_name(self, obj) -> str | None:
        if obj.validating_therapist:
            return f"{obj.validating_therapist.first_name} {obj.validating_therapist.last_name}"
        return None


class AlertValidationSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["VALIDATE", "DISMISS"])
    validation_note = serializers.CharField(
        required=False, allow_blank=True, max_length=1000
    )

    def validate_action(self, value):
        if value not in ["VALIDATE", "DISMISS"]:
            raise serializers.ValidationError("Acció no vàlida. Utilitza 'VALIDATE' o 'DISMISS'.")
        return value


class AlertNotifyContactsSerializer(serializers.Serializer):
    contact_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
    )

    def validate_contact_ids(self, value):
        if not value:
            raise serializers.ValidationError("Cal seleccionar almenys un contacte.")
        return value
