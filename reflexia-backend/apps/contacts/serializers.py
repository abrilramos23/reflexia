from rest_framework import serializers
from django.conf import settings
from django.core.mail import send_mail

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
                {"non_field_errors": ["Cal indicar com a mínim un mètode de contacte."]}
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
    id = serializers.UUIDField(read_only=True)
    support_id = serializers.UUIDField(source="support.id", read_only=True)
    first_name = serializers.CharField(source="support.first_name", read_only=True)
    last_name = serializers.CharField(source="support.last_name", read_only=True)
    email = serializers.EmailField(source="support.email", read_only=True)
    license_number = serializers.CharField(source="support.license_number", read_only=True)
    specialty = serializers.CharField(source="support.specialty", read_only=True)
    status = serializers.CharField(read_only=True)
    requested_at = serializers.DateTimeField(read_only=True)
    responded_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = SupportTherapist
        fields = (
            "id",
            "support_id",
            "first_name",
            "last_name",
            "email",
            "license_number",
            "specialty",
            "status",
            "requested_at",
            "responded_at",
        )


class SupportTherapistRequestSerializer(serializers.ModelSerializer):
    requester_id = serializers.UUIDField(source="therapist.id", read_only=True)
    first_name = serializers.CharField(source="therapist.first_name", read_only=True)
    last_name = serializers.CharField(source="therapist.last_name", read_only=True)
    email = serializers.EmailField(source="therapist.email", read_only=True)
    license_number = serializers.CharField(source="therapist.license_number", read_only=True)
    specialty = serializers.CharField(source="therapist.specialty", read_only=True)

    class Meta:
        model = SupportTherapist
        fields = (
            "id",
            "requester_id",
            "first_name",
            "last_name",
            "email",
            "license_number",
            "specialty",
            "status",
            "requested_at",
            "responded_at",
        )


class SupportTherapistResponseSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=("accept", "reject"))


class SupportTherapistCreateSerializer(serializers.Serializer):
    support_id = serializers.UUIDField()

    def validate(self, attrs):
        therapist = self.context["therapist"]

        if not therapist.organisation_memberships.filter(organisation__type='clinic').exists():
            raise serializers.ValidationError(
                {"support_id": "Aquest servei només està disponible per a professionals que pertanyen a una clínica."}
            )
        organisation = therapist.organisation

        try:
            support_therapist = Therapist.objects.get(pk=attrs["support_id"])
        except Therapist.DoesNotExist as exc:
            raise serializers.ValidationError({"support_id": "Terapeuta no trobat."}) from exc

        if therapist.pk == support_therapist.pk:
            raise serializers.ValidationError(
                {"support_id": "Un terapeuta no pot ser el seu propi terapeuta de suport."}
            )

        existing_link = SupportTherapist.objects.filter(
            therapist=therapist,
            support=support_therapist,
        ).first()
        if existing_link and existing_link.status in (
            SupportTherapist.Status.PENDING,
            SupportTherapist.Status.ACCEPTED,
        ):
            raise serializers.ValidationError(
                {"support_id": "Aquest terapeuta de suport ja té una sol·licitud pendent o acceptada."}
            )

        if support_therapist.organisation != organisation:
            raise serializers.ValidationError(
                {"support_id": "El terapeuta de suport ha de pertànyer a la mateixa clínica."}
            )

        attrs["support"] = support_therapist
        attrs["existing_link"] = existing_link
        return attrs

    def save(self, **kwargs):
        therapist = self.context["therapist"]
        existing_link = self.validated_data.get("existing_link")
        if existing_link:
            existing_link.status = SupportTherapist.Status.PENDING
            existing_link.responded_at = None
            existing_link.save(update_fields=["status", "responded_at"])
            link = existing_link
        else:
            link = SupportTherapist.objects.create(
                therapist=therapist,
                support=self.validated_data["support"],
            )

        send_support_therapist_request_email(link)
        return link


def send_support_therapist_request_email(link):
    subject = "Sol·licitud per ser terapeuta de suport a Reflexia"
    message = (
        f"Hola {link.support.first_name},\n\n"
        f"{link.therapist.first_name} {link.therapist.last_name} vol afegir-te com a terapeuta de suport a Reflexia.\n"
        "Si acceptes, podràs estar associat als seus pacients per rebre avisos en casos extrems "
        "i accedir només a la informació necessària segons la política de protecció de dades.\n\n"
        "Entra a Reflexia per acceptar o rebutjar aquesta sol·licitud."
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [link.support.email],
        fail_silently=False,
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
