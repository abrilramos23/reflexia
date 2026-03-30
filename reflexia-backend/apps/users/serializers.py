import pyotp
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import Patient, ProfessionalDirectoryEntry, Therapist, User
from apps.users.services import (
    activate_patient_account,
    build_password_reset_url,
    register_patient,
    register_therapist,
    reset_user_password,
    send_password_reset_email,
)


class UserSummarySerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    consent_accepted = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "two_factor_enabled",
            "is_active",
            "consent_accepted",
            "role",
        )

    def get_role(self, obj):
        if hasattr(obj, "therapist_profile"):
            return "therapist"
        if hasattr(obj, "patient_profile"):
            return "patient"
        if obj.is_staff:
            return "admin"
        return "user"

    def get_consent_accepted(self, obj):
        if hasattr(obj, "patient_profile"):
            return obj.patient_profile.consent_accepted
        return None


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


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        email = attrs["email"].strip().lower()
        password = attrs["password"]

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError({"detail": "Invalid email or password."}) from exc

        if not user.is_active:
            raise serializers.ValidationError({"detail": "This account is inactive. Please activate it first."})

        authenticated_user = authenticate(
            request=self.context.get("request"),
            username=user.email,
            password=password,
        )
        if authenticated_user is None:
            raise serializers.ValidationError({"detail": "Invalid email or password."})

        attrs["user"] = authenticated_user
        return attrs

    def create(self, validated_data):
        user = validated_data["user"]
        if user.two_factor_enabled:
            return {
                "login_status": "two_factor_required",
                "user": user,
                "message": "Two-factor verification is required to complete login.",
            }

        refresh = RefreshToken.for_user(user)
        login_status = "authenticated"
        if hasattr(user, "patient_profile") and not user.patient_profile.consent_accepted:
            login_status = "consent_required"

        return {
            "login_status": login_status,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": user,
        }


class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate_refresh(self, value):
        try:
            RefreshToken(value)
        except Exception as exc:
            raise serializers.ValidationError("Invalid refresh token.") from exc
        return value

    def blacklist(self):
        refresh = RefreshToken(self.validated_data["refresh"])
        refresh.blacklist()


class PatientConsentAcceptSerializer(serializers.Serializer):
    def save(self, **kwargs):
        patient = self.context["patient"]
        patient.consent_accepted = True
        patient.consent_date = timezone.now()
        patient.save(update_fields=["consent_accepted", "consent_date"])
        return patient


class PatientConsentRejectSerializer(RefreshTokenSerializer):
    def save(self, **kwargs):
        patient = self.context["patient"]
        patient.consent_accepted = False
        patient.is_active = False
        patient.save(update_fields=["consent_accepted", "is_active"])
        self.blacklist()
        return patient


class TwoFactorSetupSerializer(serializers.Serializer):
    def save(self, **kwargs):
        user = self.context["user"]
        secret = pyotp.random_base32()
        user.two_factor_pending_secret = secret
        user.save(update_fields=["two_factor_pending_secret"])

        totp = pyotp.TOTP(secret)
        return {
            "secret": secret,
            "otpauth_url": totp.provisioning_uri(
                name=user.email,
                issuer_name="Reflexia",
            ),
        }


class TwoFactorEnableSerializer(serializers.Serializer):
    code = serializers.CharField()

    def validate(self, attrs):
        user = self.context["user"]
        if not user.two_factor_pending_secret:
            raise serializers.ValidationError({"detail": "Two-factor setup has not been started."})

        totp = pyotp.TOTP(user.two_factor_pending_secret)
        if not totp.verify(attrs["code"], valid_window=1):
            raise serializers.ValidationError({"code": "Invalid verification code."})
        return attrs

    def save(self, **kwargs):
        user = self.context["user"]
        user.two_factor_secret = user.two_factor_pending_secret
        user.two_factor_pending_secret = ""
        user.two_factor_enabled = True
        user.save(update_fields=["two_factor_secret", "two_factor_pending_secret", "two_factor_enabled"])
        return user


class TwoFactorVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    code = serializers.CharField()

    def validate(self, attrs):
        email = attrs["email"].strip().lower()
        password = attrs["password"]
        code = attrs["code"]

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError({"detail": "Invalid credentials or verification code."}) from exc

        if not user.is_active:
            raise serializers.ValidationError({"detail": "This account is inactive. Please activate it first."})
        if not user.two_factor_enabled or not user.two_factor_secret:
            raise serializers.ValidationError({"detail": "Two-factor authentication is not enabled for this user."})

        authenticated_user = authenticate(
            request=self.context.get("request"),
            username=user.email,
            password=password,
        )
        if authenticated_user is None:
            raise serializers.ValidationError({"detail": "Invalid credentials or verification code."})

        totp = pyotp.TOTP(user.two_factor_secret)
        if not totp.verify(code, valid_window=1):
            raise serializers.ValidationError({"code": "Invalid verification code."})

        attrs["user"] = authenticated_user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        login_status = "authenticated"
        if hasattr(user, "patient_profile") and not user.patient_profile.consent_accepted:
            login_status = "consent_required"

        return {
            "login_status": login_status,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": user,
        }


class TwoFactorDisableSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    code = serializers.CharField()

    def validate(self, attrs):
        user = self.context["user"]
        if not user.two_factor_enabled or not user.two_factor_secret:
            raise serializers.ValidationError({"detail": "Two-factor authentication is not enabled."})

        authenticated_user = authenticate(
            request=self.context.get("request"),
            username=user.email,
            password=attrs["password"],
        )
        if authenticated_user is None:
            raise serializers.ValidationError({"detail": "Invalid password or verification code."})

        totp = pyotp.TOTP(user.two_factor_secret)
        if not totp.verify(attrs["code"], valid_window=1):
            raise serializers.ValidationError({"code": "Invalid verification code."})
        return attrs

    def save(self, **kwargs):
        user = self.context["user"]
        user.two_factor_enabled = False
        user.two_factor_secret = ""
        user.two_factor_pending_secret = ""
        user.save(update_fields=["two_factor_enabled", "two_factor_secret", "two_factor_pending_secret"])
        return user


class PasswordForgotSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def save(self, **kwargs):
        email = self.validated_data["email"].strip().lower()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return None

        reset_url = build_password_reset_url(user)
        send_password_reset_email(user=user, reset_url=reset_url)
        return user


class PasswordResetSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})
    password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})

        user = self._get_user(attrs["uid"])
        if user is None:
            raise serializers.ValidationError({"uid": "Invalid reset identifier."})
        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError({"token": "Invalid or expired reset token."})

        attrs["user"] = user
        return attrs

    def _get_user(self, uid):
        try:
            decoded_uid = force_str(urlsafe_base64_decode(uid))
            return User.objects.get(pk=decoded_uid)
        except (User.DoesNotExist, TypeError, ValueError, OverflowError):
            return None

    def save(self, **kwargs):
        user = self.validated_data["user"]
        try:
            return reset_user_password(user=user, password=self.validated_data["password"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
