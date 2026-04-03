from rest_framework import serializers

from apps.contacts.models import AssociatedContact, DefaultContact, SupportTherapist
from apps.users.models import Therapist


class AssociatedContactSerializer(serializers.ModelSerializer):
    is_default = serializers.BooleanField(required=False)

    class Meta:
        model = AssociatedContact
        fields = (
            "id",
            "name",
            "relation",
            "email",
            "phone",
            "is_default",
        )
        read_only_fields = ("id",)

    def validate(self, attrs):
        email = attrs.get("email", getattr(self.instance, "email", ""))
        phone = attrs.get("phone", getattr(self.instance, "phone", ""))

        if not email and not phone:
            raise serializers.ValidationError(
                {"non_field_errors": ["At least one contact method is required."]}
            )
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        patient = self.context.get("patient")

        if patient is None:
            data["is_default"] = False
            return data

        link = getattr(instance, "_patient_link", None)
        if link is None:
            link = DefaultContact.objects.filter(patient=patient, contact=instance).first()

        data["is_default"] = bool(link and link.is_default)
        return data

    def create(self, validated_data):
        patient = self.context["patient"]
        is_default = validated_data.pop("is_default", False)
        contact = AssociatedContact(**validated_data)
        contact.full_clean()
        contact.save()
        link = DefaultContact.objects.create(
            patient=patient,
            contact=contact,
            is_default=is_default,
        )
        contact._patient_link = link
        return contact

    def update(self, instance, validated_data):
        patient = self.context["patient"]
        is_default = validated_data.pop("is_default", None)

        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.full_clean()
        instance.save()

        if is_default is not None:
            link = DefaultContact.objects.get(patient=patient, contact=instance)
            link.is_default = is_default
            link.save(update_fields=["is_default"])
            instance._patient_link = link

        return instance


class SupportTherapistListSerializer(serializers.ModelSerializer):
    support_id = serializers.UUIDField(source="support.id", read_only=True)
    first_name = serializers.CharField(source="support.first_name", read_only=True)
    last_name = serializers.CharField(source="support.last_name", read_only=True)
    email = serializers.EmailField(source="support.email", read_only=True)
    license_number = serializers.CharField(source="support.license_number", read_only=True)
    specialty = serializers.CharField(source="support.specialty", read_only=True)

    class Meta:
        model = SupportTherapist
        fields = (
            "support_id",
            "first_name",
            "last_name",
            "email",
            "license_number",
            "specialty",
        )


class SupportTherapistCreateSerializer(serializers.Serializer):
    support_id = serializers.UUIDField()

    def validate(self, attrs):
        therapist = self.context["therapist"]

        try:
            support_therapist = Therapist.objects.get(pk=attrs["support_id"])
        except Therapist.DoesNotExist as exc:
            raise serializers.ValidationError({"support_id": "Therapist not found."}) from exc

        if therapist.pk == support_therapist.pk:
            raise serializers.ValidationError(
                {"support_id": "A therapist cannot be their own support therapist."}
            )

        if SupportTherapist.objects.filter(
            therapist=therapist,
            support=support_therapist,
        ).exists():
            raise serializers.ValidationError(
                {"support_id": "This support therapist is already assigned."}
            )

        attrs["support"] = support_therapist
        return attrs

    def save(self, **kwargs):
        therapist = self.context["therapist"]
        return SupportTherapist.objects.create(
            therapist=therapist,
            support=self.validated_data["support"],
        )


class AvailableTherapistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Therapist
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "license_number",
            "specialty",
        )
