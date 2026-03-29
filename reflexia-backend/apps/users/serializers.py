from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers

from apps.users.models import Patient, ProfessionalDirectoryEntry, Therapist, User
from apps.users.services import activate_patient_account, register_patient, register_therapist


class TherapistRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})
    password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = Therapist
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "password",
            "password_confirm",
            "license_number",
            "specialty",
            "registration_date",
            "two_factor_enabled",
        )
        read_only_fields = ("id", "registration_date", "two_factor_enabled")

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_license_number(self, value):
        normalized_value = value.strip().upper()

        if not ProfessionalDirectoryEntry.objects.filter(license_number=normalized_value).exists():
            raise serializers.ValidationError("This license number is not present in the Catalonia directory.")
        if Therapist.objects.filter(license_number=normalized_value).exists():
            raise serializers.ValidationError("This license number is already assigned to another therapist.")
        return normalized_value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        try:
            return register_therapist(**validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc


class PatientRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "birth_date",
            "consent_accepted",
            "consent_date",
            "registration_date",
            "two_factor_enabled",
        )
        read_only_fields = ("id", "registration_date", "two_factor_enabled")

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        consent_accepted = attrs.get("consent_accepted", False)
        consent_date = attrs.get("consent_date")
        if consent_accepted and consent_date is None:
            raise serializers.ValidationError(
                {"consent_date": "Consent date is required when consent is accepted."}
            )
        return attrs

    def create(self, validated_data):
        therapist = self.context["therapist"]
        patient, activation_url = register_patient(therapist=therapist, **validated_data)
        self.context["activation_url"] = activation_url
        return patient


class PatientActivationSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})
    password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})

        patient = self._get_patient(attrs["uid"])
        if patient is None:
            raise serializers.ValidationError({"uid": "Invalid activation identifier."})
        if not default_token_generator.check_token(patient, attrs["token"]):
            raise serializers.ValidationError({"token": "Invalid or expired activation token."})

        attrs["patient"] = patient
        return attrs

    def _get_patient(self, uid):
        try:
            decoded_uid = force_str(urlsafe_base64_decode(uid))
            return Patient.objects.get(pk=decoded_uid)
        except (Patient.DoesNotExist, TypeError, ValueError, OverflowError):
            return None

    def save(self, **kwargs):
        patient = self.validated_data["patient"]
        try:
            return activate_patient_account(patient=patient, password=self.validated_data["password"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
