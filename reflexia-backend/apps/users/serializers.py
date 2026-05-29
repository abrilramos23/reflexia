import pyotp
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field

from apps.users.models import (
    InvitacioOrganitzacio,
    Organisation,
    OrganisationMember,
    Patient,
    ProfessionalDirectoryEntry,
    Therapist,
    User,
)


def validate_therapist_name_against_directory(license_number, first_name, last_name):
    """
    Validates that first_name and last_name match the directory entry for the license_number.
    Uses word-level, case-insensitive matching.

    Returns the ProfessionalDirectoryEntry if valid, raises ValidationError if names don't match.
    """
    try:
        directory_entry = ProfessionalDirectoryEntry.objects.get(
            license_number=license_number.strip().upper()
        )
    except ProfessionalDirectoryEntry.DoesNotExist:
        return None

    directory_name_words = set(directory_entry.complete_name.strip().split())
    user_name = f"{first_name} {last_name}".strip().upper()
    user_name_words = set(user_name.split())

    if not user_name_words.issubset(directory_name_words):
        missing_words = user_name_words - directory_name_words
        raise serializers.ValidationError(
            f"The name provided does not match the directory entry. "
            f"Directory has: {directory_entry.complete_name}. "
            f"Missing: {', '.join(missing_words)}"
        )

    return directory_entry
from apps.users.services import (
    activate_user_account,
    build_password_reset_url,
    change_user_password,
    deactivate_patient_by_therapist,
    delete_user_account,
    register_patient,
    register_therapist,
    create_organisation_invitation,
    reset_user_password,
    send_password_reset_email,
    update_user_profile,
)


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ("id", "name", "type", "is_active", "created_at")


class OrganisationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ("name", "type", "is_active")
        extra_kwargs = {
            "name": {"required": False},
            "type": {"required": False},
            "is_active": {"required": False},
        }


class OrganisationMemberSerializer(serializers.ModelSerializer):
    organisation = OrganisationSerializer(read_only=True)

    class Meta:
        model = OrganisationMember
        fields = ("organisation", "is_admin", "joined_at")


class UserSummarySerializer(serializers.ModelSerializer):
    role_label = serializers.CharField(source="get_role_display", read_only=True)
    organisation = serializers.SerializerMethodField()
    is_clinic_admin = serializers.BooleanField(read_only=True)
    memberships = OrganisationMemberSerializer(source="organisation_memberships", many=True, read_only=True)
    consent_accepted = serializers.SerializerMethodField()
    specialty = serializers.SerializerMethodField()
    license_number = serializers.SerializerMethodField()
    legal_terms_accepted = serializers.BooleanField(read_only=True)
    legal_terms_accepted_at = serializers.DateTimeField(read_only=True)
    legal_terms_version = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "role",
            "role_label",
            "organisation",
            "is_clinic_admin",
            "memberships",
            "registration_date",
            "two_factor_enabled",
            "is_active",
            "consent_accepted",
            "legal_terms_accepted",
            "legal_terms_accepted_at",
            "legal_terms_version",
            "license_number",
            "specialty",
        )

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_consent_accepted(self, obj):
        return obj.legal_terms_accepted

    @extend_schema_field(OrganisationSerializer)
    def get_organisation(self, obj):
        organisation = obj.organisation
        if organisation is None:
            return None
        return OrganisationSerializer(organisation).data

    @extend_schema_field(OpenApiTypes.STR)
    def get_specialty(self, obj):
        if hasattr(obj, "therapist_profile"):
            return obj.therapist_profile.specialty
        return None

    @extend_schema_field(OpenApiTypes.STR)
    def get_license_number(self, obj):
        if hasattr(obj, "therapist_profile"):
            return obj.therapist_profile.license_number
        return None


class TherapistRegistrationSerializer(serializers.ModelSerializer):
    class RegistrationPath:
        INDEPENDENT = "independent"
        CREATE_CLINIC = "create_clinic"
        JOIN_ORGANISATION = "join_organisation"

    registration_path = serializers.ChoiceField(
        choices=(
            RegistrationPath.INDEPENDENT,
            RegistrationPath.CREATE_CLINIC,
            RegistrationPath.JOIN_ORGANISATION,
        ),
        write_only=True,
    )
    organisation_name = serializers.CharField(max_length=255, required=False, write_only=True)
    invitation_token = serializers.CharField(max_length=36, required=False, write_only=True)

    class Meta:
        model = Therapist
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "license_number",
            "specialty",
            "registration_path",
            "organisation_name",
            "invitation_token",
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
        license_number = attrs.get("license_number")
        first_name = attrs.get("first_name")
        last_name = attrs.get("last_name")

        if license_number and first_name and last_name:
            validate_therapist_name_against_directory(license_number, first_name, last_name)

        registration_path = attrs.get("registration_path")
        organisation_name = attrs.get("organisation_name", "").strip()
        invitation_token = attrs.get("invitation_token", "").strip()

        if registration_path == self.RegistrationPath.CREATE_CLINIC and not organisation_name:
            raise serializers.ValidationError(
                {"organisation_name": "El nom de l'organització és obligatori per crear una clínica."}
            )

        if registration_path == self.RegistrationPath.JOIN_ORGANISATION:
            if not invitation_token:
                raise serializers.ValidationError(
                    {"invitation_token": "El token d'invitació és obligatori per unir-se a una organització."}
                )
            invitation = InvitacioOrganitzacio.objects.filter(token=invitation_token).first()
            if invitation is None or not invitation.is_usable:
                raise serializers.ValidationError(
                    {"invitation_token": "La invitació no és vàlida, ja s'ha usat o ha caducat."}
                )
            if invitation.idOrganitzacio.type != Organisation.Type.CLINIC:
                raise serializers.ValidationError(
                    {"invitation_token": "La invitació no pertany a una organització clínica."}
                )
            if invitation.email and invitation.email.lower() != attrs.get("email", "").lower():
                raise serializers.ValidationError(
                    {"email": "Aquest token d'invitació està vinculat a un altre correu electrònic."}
                )

        if registration_path != self.RegistrationPath.JOIN_ORGANISATION and invitation_token:
            raise serializers.ValidationError(
                {"invitation_token": "El token només es pot usar en el camí d'unir-se a una organització."}
            )

        attrs["organisation_name"] = organisation_name

        return attrs

    def create(self, validated_data):
        try:
            therapist, activation_url = register_therapist(**validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages) from exc
        self.context["activation_url"] = activation_url
        return therapist


class PatientTherapistOptionSerializer(serializers.ModelSerializer):
    organisation_name = serializers.CharField(source="organisation.name", read_only=True)

    class Meta:
        model = Therapist
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "license_number",
            "specialty",
            "organisation_name",
        )


class PatientTherapistChangeSerializer(serializers.Serializer):
    therapist_id = serializers.UUIDField()

    def validate(self, attrs):
        patient = self.context["patient"]
        try:
            new_therapist = Therapist.objects.get(pk=attrs["therapist_id"], is_active=True)
        except Therapist.DoesNotExist as exc:
            raise serializers.ValidationError({"therapist_id": "Therapist not found."}) from exc

        active_link = (
            patient.therapist_links.filter(is_active=True)
            .select_related("therapist")
            .first()
        )
        if active_link is None:
            raise serializers.ValidationError(
                {"therapist_id": "Aquest pacient no té cap terapeuta actiu assignat."}
            )
        if active_link.therapist_id == new_therapist.pk:
            raise serializers.ValidationError(
                {"therapist_id": "Aquest terapeuta ja és el teu terapeuta actual."}
            )
        current_organisation = active_link.therapist.organisation
        new_organisation = new_therapist.organisation
        if (
            current_organisation is None
            or new_organisation is None
            or current_organisation.id != new_organisation.id
        ):
            raise serializers.ValidationError(
                {
                    "therapist_id": (
                        "Per protecció de dades, el canvi automàtic només està permès "
                        "dins la mateixa organització clínica."
                    )
                }
            )

        attrs["current_link"] = active_link
        attrs["new_therapist"] = new_therapist
        return attrs

    def save(self, **kwargs):
        from apps.users.services import change_patient_therapist

        return change_patient_therapist(
            patient=self.context["patient"],
            current_link=self.validated_data["current_link"],
            new_therapist=self.validated_data["new_therapist"],
        )


class InvitacioOrganitzacioSerializer(serializers.ModelSerializer):
    idOrganitzacio = serializers.UUIDField(source="idOrganitzacio.id", read_only=True)

    class Meta:
        model = InvitacioOrganitzacio
        fields = ("token", "email", "idOrganitzacio", "dataCreacio", "dataCaducitat", "usat")
        read_only_fields = ("token", "idOrganitzacio", "dataCreacio", "usat")


class InvitacioOrganitzacioCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    dataCaducitat = serializers.DateTimeField(required=False, allow_null=True)

    def validate_email(self, value):
        normalized_value = User.objects.normalize_email(value)
        if User.objects.filter(email__iexact=normalized_value).exists():
            raise serializers.ValidationError("Ja existeix un usuari amb aquest correu electrònic.")
        return normalized_value

    def validate_dataCaducitat(self, value):
        if value is not None and value <= timezone.now():
            raise serializers.ValidationError("La data de caducitat ha de ser futura.")
        return value

    def create(self, validated_data):
        admin = self.context["admin"]
        try:
            return create_organisation_invitation(
                admin=admin,
                email=validated_data["email"],
                dataCaducitat=validated_data.get("dataCaducitat"),
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages) from exc


class TherapistAdminUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    email = serializers.EmailField(required=False)
    license_number = serializers.CharField(max_length=100, required=False)
    specialty = serializers.CharField(max_length=150, required=False)
    organisation_id = serializers.UUIDField(required=False, allow_null=True)
    is_admin = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)

    def validate_email(self, value):
        therapist = self.context["therapist"]
        if User.objects.filter(email__iexact=value).exclude(pk=therapist.pk).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_license_number(self, value):
        therapist = self.context["therapist"]
        normalized_value = value.strip().upper()

        if not ProfessionalDirectoryEntry.objects.filter(license_number=normalized_value).exists():
            raise serializers.ValidationError("This license number is not present in the Catalonia directory.")
        if Therapist.objects.filter(license_number=normalized_value).exclude(pk=therapist.pk).exists():
            raise serializers.ValidationError("This license number is already assigned to another therapist.")
        return normalized_value

    def validate(self, attrs):
        therapist = self.context["therapist"]
        license_number = attrs.get("license_number")
        first_name = attrs.get("first_name")
        last_name = attrs.get("last_name")

        if license_number:
            if not first_name:
                first_name = therapist.first_name
            if not last_name:
                last_name = therapist.last_name

            validate_therapist_name_against_directory(license_number, first_name, last_name)

        return attrs

    def validate_organisation_id(self, value):
        if value is None:
            return None

        try:
            return Organisation.objects.get(pk=value)
        except Organisation.DoesNotExist as exc:
            raise serializers.ValidationError("Organisation not found.") from exc


class PatientRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "birth_date",
            "registration_date",
            "two_factor_enabled",
        )
        read_only_fields = ("id", "registration_date", "two_factor_enabled")

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        therapist = self.context["therapist"]
        patient, activation_url = register_patient(therapist=therapist, **validated_data)
        self.context["activation_url"] = activation_url
        return patient


class TherapistPatientSummarySerializer(serializers.ModelSerializer):
    consent_accepted = serializers.BooleanField(source="legal_terms_accepted", read_only=True)
    consent_date = serializers.DateTimeField(source="legal_terms_accepted_at", read_only=True)

    class Meta:
        model = Patient
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "birth_date",
            "is_active",
            "consent_accepted",
            "consent_date",
            "registration_date",
        )


class AccountActivationSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})
    password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})

        user = self._get_user(attrs["uid"])
        if user is None:
            raise serializers.ValidationError({"uid": "Invalid activation identifier."})
        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError({"token": "Invalid or expired activation token."})

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
            return activate_user_account(user=user, password=self.validated_data["password"])
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
        if not user.legal_terms_accepted:
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
        user = self.context["user"]
        user.legal_terms_accepted = True
        user.legal_terms_accepted_at = timezone.now()
        user.legal_terms_version = User.LEGAL_TERMS_VERSION
        user.save(update_fields=["legal_terms_accepted", "legal_terms_accepted_at", "legal_terms_version"])
        return user


class PatientConsentRejectSerializer(RefreshTokenSerializer):
    def save(self, **kwargs):
        user = self.context["user"]
        user.legal_terms_accepted = False
        user.is_active = False
        user.save(update_fields=["legal_terms_accepted", "is_active"])
        self.blacklist()
        return user


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
        if not user.legal_terms_accepted:
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


class ProfileUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    specialty = serializers.CharField(required=False, allow_blank=False)

    def validate(self, attrs):
        user = self.context["user"]

        if hasattr(user, "patient_profile"):
            allowed_fields = {"email"}
        elif hasattr(user, "therapist_profile"):
            allowed_fields = {"email", "specialty"}
        else:
            allowed_fields = {"email"}

        invalid_fields = set(attrs.keys()) - allowed_fields
        if invalid_fields:
            raise serializers.ValidationError(
                {field: "This field cannot be updated for this user." for field in invalid_fields}
            )

        email = attrs.get("email")
        if email and User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})

        return attrs

    def save(self, **kwargs):
        user = self.context["user"]
        return update_user_profile(
            user=user,
            email=self.validated_data.get("email"),
            specialty=self.validated_data.get("specialty"),
        )


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})
    new_password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        return attrs

    def save(self, **kwargs):
        user = self.context["user"]
        try:
            return change_user_password(
                user=user,
                current_password=self.validated_data["current_password"],
                new_password=self.validated_data["new_password"],
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc


class DeleteAccountSerializer(RefreshTokenSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        attrs = super().validate(attrs)
        user = self.context["user"]
        if not user.check_password(attrs["password"]):
            raise serializers.ValidationError({"password": "La contrasenya actual no és correcta."})
        return attrs

    def save(self, **kwargs):
        user = self.context["user"]
        try:
            deleted_user = delete_user_account(user=user)
        except DjangoValidationError as exc:
            error_data = exc.message_dict
            patients = error_data.get("patients")
            if isinstance(patients, dict):
                error_data["patients"] = [patients]
            raise serializers.ValidationError(error_data) from exc
        self.blacklist()
        return deleted_user


class TherapistPatientDeactivateSerializer(serializers.Serializer):
    patient_id = serializers.UUIDField()

    def validate(self, attrs):
        therapist = self.context["therapist"]
        try:
            patient = Patient.objects.get(pk=attrs["patient_id"])
        except Patient.DoesNotExist as exc:
            raise serializers.ValidationError({"patient_id": "Patient not found."}) from exc

        attrs["patient"] = patient
        attrs["therapist"] = therapist
        return attrs

    def save(self, **kwargs):
        try:
            return deactivate_patient_by_therapist(
                therapist=self.validated_data["therapist"],
                patient=self.validated_data["patient"],
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc
