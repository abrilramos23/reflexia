from pathlib import Path
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404
from rest_framework import status
from django.conf import settings
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, inline_serializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers

from apps.users.permissions import IsTherapistUser, IsClinicAdminUser
from apps.users.models import User, Patient, Therapist, Organisation, OrganisationMember
from apps.users.serializers import (
    AccountActivationSerializer,
    ChangePasswordSerializer,
    DeleteAccountSerializer,
    LoginSerializer,
    PasswordForgotSerializer,
    PasswordResetSerializer,
    PatientConsentAcceptSerializer,
    PatientConsentRejectSerializer,
    PatientRegistrationSerializer,
    RefreshTokenSerializer,
    ProfileUpdateSerializer,
    TherapistRegistrationSerializer,
    TherapistPatientDeactivateSerializer,
    TherapistPatientSummarySerializer,
    TwoFactorDisableSerializer,
    TwoFactorEnableSerializer,
    TwoFactorSetupSerializer,
    TwoFactorVerifySerializer,
    UserSummarySerializer,
    OrganisationSerializer,
    OrganisationUpdateSerializer,
    InvitacioOrganitzacioCreateSerializer,
    InvitacioOrganitzacioSerializer,
    TherapistAdminUpdateSerializer,
)
from apps.users.services import delete_user_account


class TherapistRegistrationView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Users"],
        summary="Registrar terapeuta",
        request=TherapistRegistrationSerializer,
        responses={
            201: inline_serializer(
                name="TherapistRegistrationResponse",
                fields={
                    "id": serializers.UUIDField(),
                    "first_name": serializers.CharField(),
                    "last_name": serializers.CharField(),
                    "email": serializers.EmailField(),
                    "license_number": serializers.CharField(),
                    "specialty": serializers.CharField(),
                    "is_clinic_admin": serializers.BooleanField(),
                    "organisation": OrganisationSerializer(),
                    "registration_date": serializers.DateTimeField(),
                    "two_factor_enabled": serializers.BooleanField(),
                    "activation_email_sent": serializers.BooleanField(),
                    "activation_url": serializers.CharField(required=False),
                },
            ),
        },
        examples=[
            OpenApiExample(
                "Crear terapeuta",
                value={
                    "first_name": "Marta",
                    "last_name": "Lopez",
                    "email": "therapist@example.com",
                    "license_number": "21039",
                    "specialty": "Psicologia clínica",
                    "registration_path": "create_clinic",
                    "organisation_name": "Centre Reflexia",
                },
                request_only=True,
            )
        ],
    )
    def post(self, request):
        serializer = TherapistRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        therapist = serializer.save()

        response_serializer = TherapistRegistrationSerializer(therapist)
        response_data = {
            **response_serializer.data,
            "is_clinic_admin": therapist.is_clinic_admin,
            "organisation": OrganisationSerializer(therapist.organisation).data if therapist.organisation else None,
            "activation_email_sent": True,
        }
        if settings.DEBUG:
            response_data["activation_url"] = serializer.context.get("activation_url")
        return Response(response_data, status=status.HTTP_201_CREATED)


class InvitacioOrganitzacioCreateView(APIView):
    permission_classes = [IsClinicAdminUser]

    @extend_schema(
        tags=["Users"],
        summary="Crear una invitació d'organització",
        request=InvitacioOrganitzacioCreateSerializer,
        responses={201: InvitacioOrganitzacioSerializer},
    )
    def post(self, request):
        serializer = InvitacioOrganitzacioCreateSerializer(
            data=request.data,
            context={"admin": request.user},
        )
        serializer.is_valid(raise_exception=True)
        invitation = serializer.save()
        return Response(
            InvitacioOrganitzacioSerializer(invitation).data,
            status=status.HTTP_201_CREATED,
        )


class PatientRegistrationView(APIView):
    permission_classes = [IsTherapistUser]

    @extend_schema(
        tags=["Users"],
        summary="Registrar pacient",
        request=PatientRegistrationSerializer,
        responses={
            201: inline_serializer(
                name="PatientRegistrationResponse",
                fields={
                    "id": serializers.UUIDField(),
                    "first_name": serializers.CharField(),
                    "last_name": serializers.CharField(),
                    "email": serializers.EmailField(),
                    "birth_date": serializers.DateField(),
                    "consent_accepted": serializers.BooleanField(),
                    "consent_date": serializers.DateTimeField(allow_null=True),
                    "registration_date": serializers.DateTimeField(),
                    "two_factor_enabled": serializers.BooleanField(),
                    "activation_email_sent": serializers.BooleanField(),
                    "activation_url": serializers.CharField(required=False),
                },
            ),
        },
        examples=[
            OpenApiExample(
                "Crear pacient",
                value={
                    "first_name": "Paula",
                    "last_name": "Sanchez",
                    "email": "patient@example.com",
                    "birth_date": "2001-01-10",
                    "consent_accepted": False,
                },
                request_only=True,
            )
        ],
    )
    def post(self, request):
        serializer = PatientRegistrationSerializer(
            data=request.data,
            context={"therapist": request.user.therapist_profile},
        )
        serializer.is_valid(raise_exception=True)
        patient = serializer.save()

        response_serializer = PatientRegistrationSerializer(patient)
        response_data = {
            **response_serializer.data,
            "activation_email_sent": True,
        }
        if settings.DEBUG:
            response_data["activation_url"] = serializer.context.get("activation_url")
        return Response(response_data, status=status.HTTP_201_CREATED)


class AccountActivationView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Users"],
        summary="Activar compte",
        request=AccountActivationSerializer,
        responses={
            200: inline_serializer(
                name="AccountActivationResponse",
                fields={
                    "id": serializers.UUIDField(),
                    "email": serializers.EmailField(),
                    "is_active": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            ),
        },
    )
    def post(self, request):
        serializer = AccountActivationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "id": str(user.pk),
                "email": user.email,
                "is_active": user.is_active,
                "message": "Account activated successfully.",
            },
            status=status.HTTP_200_OK,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Users"],
        summary="Iniciar sessio",
        request=LoginSerializer,
        responses={
            200: inline_serializer(
                name="LoginResponse",
                fields={
                    "login_status": serializers.ChoiceField(
                        choices=["authenticated", "consent_required", "two_factor_required"]
                    ),
                    "user": UserSummarySerializer(),
                    "access": serializers.CharField(required=False, allow_null=True),
                    "refresh": serializers.CharField(required=False, allow_null=True),
                    "message": serializers.CharField(required=False, allow_null=True),
                },
            ),
        },
        examples=[
            OpenApiExample(
                "Login amb 2FA",
                value={
                    "login_status": "two_factor_required",
                    "user": {
                        "id": "11111111-1111-1111-1111-111111111111",
                        "first_name": "Marta",
                        "last_name": "Lopez",
                        "email": "therapist@example.com",
                        "two_factor_enabled": True,
                        "is_active": True,
                        "consent_accepted": None,
                        "role": "therapist",
                    },
                    "access": None,
                    "refresh": None,
                    "message": "Two-factor verification is required to complete login.",
                },
                response_only=True,
            )
        ],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        login_result = serializer.save()

        return Response(
            {
                "login_status": login_result["login_status"],
                "user": UserSummarySerializer(login_result["user"]).data,
                "access": login_result.get("access"),
                "refresh": login_result.get("refresh"),
                "message": login_result.get("message"),
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Users"],
        summary="Tancar sessio",
        request=RefreshTokenSerializer,
        responses={200: inline_serializer(name="LogoutResponse", fields={"message": serializers.CharField()})},
    )
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.blacklist()
        return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)


class PasswordForgotView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Users"],
        summary="Sollicitar recuperacio de contrasenya",
        request=PasswordForgotSerializer,
        responses={
            200: inline_serializer(name="PasswordForgotResponse", fields={"message": serializers.CharField()}),
        },
        examples=[
            OpenApiExample(
                "Recuperar contrasenya",
                value={"email": "user@example.com"},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        serializer = PasswordForgotSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "message": "If the email exists, a password reset link has been sent.",
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Users"],
        summary="Restablir contrasenya",
        request=PasswordResetSerializer,
        responses={
            200: inline_serializer(name="PasswordResetResponse", fields={"message": serializers.CharField()}),
        },
    )
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "message": "Password updated successfully.",
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Users"],
        summary="Obtenir usuari autenticat",
        responses={200: UserSummarySerializer},
    )
    def get(self, request):
        return Response(UserSummarySerializer(request.user).data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Users"],
        summary="Actualitzar perfil",
        request=ProfileUpdateSerializer,
        responses={
            200: inline_serializer(
                name="ProfileUpdateResponse",
                fields={
                    "message": serializers.CharField(),
                    "user": UserSummarySerializer(),
                },
            )
        },
    )
    def patch(self, request):
        serializer = ProfileUpdateSerializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "Profile updated successfully.",
                "user": UserSummarySerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Users"],
        summary="Canviar contrasenya",
        request=ChangePasswordSerializer,
        responses={
            200: inline_serializer(name="ChangePasswordResponse", fields={"message": serializers.CharField()}),
        },
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "message": "Password updated successfully.",
            },
            status=status.HTTP_200_OK,
        )


class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Users"],
        summary="Eliminar compte",
        request=DeleteAccountSerializer,
        responses={
            200: inline_serializer(name="DeleteAccountResponse", fields={"message": serializers.CharField()}),
            400: OpenApiResponse(
                response=inline_serializer(
                    name="DeleteAccountBlockedResponse",
                    fields={
                        "assigned_patients": serializers.ListField(child=serializers.CharField()),
                        "patients": serializers.JSONField(),
                    },
                ),
                description="El terapeuta encara te pacients actius assignats.",
            ),
        },
        examples=[
            OpenApiExample(
                "Eliminar compte",
                value={
                    "password": "StrongPass123!",
                    "refresh": "jwt-refresh-token",
                },
                request_only=True,
            )
        ],
    )
    def post(self, request):
        serializer = DeleteAccountSerializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "message": "Account deleted successfully.",
            },
            status=status.HTTP_200_OK,
        )


class TherapistPatientDeactivateView(APIView):
    permission_classes = [IsTherapistUser]

    @extend_schema(
        tags=["Users"],
        summary="Donar de baixa un pacient assignat",
        request=TherapistPatientDeactivateSerializer,
        responses={
            200: inline_serializer(
                name="PatientDeactivateResponse",
                fields={
                    "message": serializers.CharField(),
                    "patient_id": serializers.UUIDField(),
                },
            ),
        },
    )
    def post(self, request):
        serializer = TherapistPatientDeactivateSerializer(
            data=request.data,
            context={"therapist": request.user.therapist_profile},
        )
        serializer.is_valid(raise_exception=True)
        patient = serializer.save()
        return Response(
            {
                "message": "Patient deactivated successfully.",
                "patient_id": str(patient.pk),
            },
            status=status.HTTP_200_OK,
        )


class TherapistPatientListView(APIView):
    permission_classes = [IsTherapistUser]

    @extend_schema(
        tags=["Users"],
        summary="Llistar pacients assignats al terapeuta",
        responses={200: TherapistPatientSummarySerializer(many=True)},
    )
    def get(self, request):
        patients = Patient.objects.filter(
            therapist_links__therapist=request.user.therapist_profile
        ).order_by("first_name", "last_name")
        return Response(
            TherapistPatientSummarySerializer(patients, many=True).data,
            status=status.HTTP_200_OK,
        )


class TherapistPatientDetailView(APIView):
    permission_classes = [IsTherapistUser]

    @extend_schema(
        tags=["Users"],
        summary="Obtenir detall d'un pacient assignat al terapeuta",
        responses={200: TherapistPatientSummarySerializer},
    )
    def get(self, request, patient_id):
        patient = get_object_or_404(
            Patient,
            pk=patient_id,
            therapist_links__therapist=request.user.therapist_profile
        )
        return Response(
            TherapistPatientSummarySerializer(patient).data,
            status=status.HTTP_200_OK,
        )


class TherapistDashboardView(APIView):
    permission_classes = [IsTherapistUser]

    @extend_schema(
        tags=["Users"],
        summary="Obtenir dades del tauler del terapeuta",
        responses={200: inline_serializer(
            name="TherapistDashboardData",
            fields={
                "metrics": inline_serializer(
                    name="TherapistMetrics",
                    fields={
                        "total_patients": serializers.IntegerField(),
                        "active_patients": serializers.IntegerField(),
                        "total_entries": serializers.IntegerField(),
                        "entries_today": serializers.IntegerField(),
                        "pending_analyses": serializers.IntegerField(),
                    }
                ),
                "recent_activity": serializers.ListField(child=serializers.DictField())
            }
        )}
    )
    def get(self, request):
        therapist = request.user.therapist_profile
        patients = Patient.objects.filter(therapist_links__therapist=therapist)
        
        # Metrics
        active_patients = patients.filter(is_active=True)
        
        from apps.entries.models import JournalEntry
        from apps.analysis.models import EmotionalAnalysis
        
        patient_ids = patients.values_list('id', flat=True)
        total_entries = JournalEntry.objects.filter(patient_id__in=patient_ids).count()
        
        today = timezone.now().date()
        entries_today = JournalEntry.objects.filter(
            patient_id__in=patient_ids,
            created_at__date=today
        ).count()
        
        pending_analyses = EmotionalAnalysis.objects.filter(
            entry__patient_id__in=patient_ids,
            reviewed_by_therapist=False
        ).count()
        
        # Recent Activity
        recent_entries = JournalEntry.objects.filter(
            patient_id__in=patient_ids
        ).select_related('patient', 'analysis').order_by('-updated_at')[:5]
        
        recent_activity = []
        for entry in recent_entries:
            recent_activity.append({
                "id": str(entry.id),
                "patient_id": str(entry.patient_id),
                "patient_name": f"{entry.patient.first_name} {entry.patient.last_name}",
                "preview": self._get_preview(entry.content),
                "created_at": entry.created_at,
                "updated_at": entry.updated_at,
                "primary_emotion": entry.analysis.primary_emotion if hasattr(entry, 'analysis') else None,
                "risk_level": entry.analysis.risk_level if hasattr(entry, 'analysis') else None,
            })

        return Response({
            "metrics": {
                "total_patients": patients.count(),
                "active_patients": active_patients.count(),
                "total_entries": total_entries,
                "entries_today": entries_today,
                "pending_analyses": pending_analyses,
            },
            "recent_activity": recent_activity
        })

    def _get_preview(self, content):
        from django.utils.html import strip_tags
        plain_text = strip_tags(content or "").strip()
        if len(plain_text) <= 100:
            return plain_text
        return f"{plain_text[:100]}..."


class PatientConsentAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Users"],
        summary="Acceptar consentiment informat",
        request=None,
        responses={
            200: inline_serializer(
                name="PatientConsentAcceptResponse",
                fields={
                    "message": serializers.CharField(),
                    "user": UserSummarySerializer(),
                },
            ),
        },
    )
    def post(self, request):
        if not hasattr(request.user, "patient_profile"):
            return Response(
                {"detail": "Only patients can accept informed consent."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = PatientConsentAcceptSerializer(context={"patient": request.user.patient_profile})
        patient = serializer.save()
        return Response(
            {
                "message": "Consent accepted successfully.",
                "user": UserSummarySerializer(patient).data,
            },
            status=status.HTTP_200_OK,
        )


class PatientConsentRejectView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Users"],
        summary="Rebutjar consentiment informat",
        request=RefreshTokenSerializer,
        responses={200: inline_serializer(name="PatientConsentRejectResponse", fields={"message": serializers.CharField()})},
    )
    def post(self, request):
        if not hasattr(request.user, "patient_profile"):
            return Response(
                {"detail": "Only patients can reject informed consent."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = PatientConsentRejectSerializer(
            data=request.data,
            context={"patient": request.user.patient_profile},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "message": "Consent rejected. The account has been deactivated.",
            },
            status=status.HTTP_200_OK,
        )


class TwoFactorSetupView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Users"],
        summary="Iniciar configuracio 2FA",
        request=None,
        responses={
            200: inline_serializer(
                name="TwoFactorSetupResponse",
                fields={
                    "secret": serializers.CharField(),
                    "otpauth_url": serializers.CharField(),
                },
            ),
        },
    )
    def post(self, request):
        serializer = TwoFactorSetupSerializer(context={"user": request.user})
        setup_data = serializer.save()
        return Response(setup_data, status=status.HTTP_200_OK)


class TwoFactorEnableView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Users"],
        summary="Activar 2FA",
        request=TwoFactorEnableSerializer,
        responses={
            200: inline_serializer(
                name="TwoFactorEnableResponse",
                fields={
                    "message": serializers.CharField(),
                    "user": UserSummarySerializer(),
                },
            )
        },
    )
    def post(self, request):
        serializer = TwoFactorEnableSerializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "Two-factor authentication enabled successfully.",
                "user": UserSummarySerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class TwoFactorVerifyView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Users"],
        summary="Verificar codi 2FA en login",
        request=TwoFactorVerifySerializer,
        responses={
            200: inline_serializer(
                name="TwoFactorVerifyResponse",
                fields={
                    "login_status": serializers.ChoiceField(choices=["authenticated", "consent_required"]),
                    "user": UserSummarySerializer(),
                    "access": serializers.CharField(),
                    "refresh": serializers.CharField(),
                },
            ),
        },
    )
    def post(self, request):
        serializer = TwoFactorVerifySerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        login_result = serializer.save()
        return Response(
            {
                "login_status": login_result["login_status"],
                "user": UserSummarySerializer(login_result["user"]).data,
                "access": login_result["access"],
                "refresh": login_result["refresh"],
            },
            status=status.HTTP_200_OK,
        )


class TwoFactorDisableView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Users"],
        summary="Desactivar 2FA",
        request=TwoFactorDisableSerializer,
        responses={
            200: inline_serializer(
                name="TwoFactorDisableResponse",
                fields={
                    "message": serializers.CharField(),
                    "user": UserSummarySerializer(),
                },
            )
        },
    )
    def post(self, request):
        serializer = TwoFactorDisableSerializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "Two-factor authentication disabled successfully.",
                "user": UserSummarySerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class ConsentDocumentView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Users"],
        summary="Descarregar document de consentiment",
        responses={
            200: OpenApiResponse(description="Fitxer PDF del consentiment informat."),
        },
    )
    def get(self, request):
        pdf_path = Path(__file__).resolve().parent / "data" / "Reflexia_ Consentiment Informat.pdf"
        if not pdf_path.exists():
            raise Http404("Consent document not found.")

        return FileResponse(
            pdf_path.open("rb"),
            content_type="application/pdf",
            filename="Reflexia_Consentiment_Informat.pdf",
        )


class ClinicStatsView(APIView):
    permission_classes = [IsClinicAdminUser]

    @extend_schema(
        tags=["Users"],
        summary="Obtenir estadístiques de la clínica",
        responses={200: inline_serializer(
            name="ClinicStats",
            fields={
                "total_therapists": serializers.IntegerField(),
                "total_patients": serializers.IntegerField(),
            }
        )}
    )
    def get(self, request):
        membership = request.user.organisation_memberships.filter(is_admin=True).first()
        if not membership:
            return Response({"detail": "User is not an admin of any organisation."}, status=status.HTTP_403_FORBIDDEN)
        
        organisation = membership.organisation
        
        stats = {
            "total_therapists": User.objects.filter(
                organisation_memberships__organisation=organisation,
                role=User.Role.THERAPIST,
            ).distinct().count(),
            "total_patients": Patient.objects.filter(
                therapist_links__therapist__organisation_memberships__organisation=organisation,
                therapist_links__is_active=True,
                is_active=True,
            ).distinct().count(),
        }
        return Response(stats)


def _validation_detail(exc):
    if hasattr(exc, "message_dict"):
        return exc.message_dict
    if hasattr(exc, "messages"):
        return {"detail": exc.messages}
    return {"detail": str(exc)}


def _clinic_admin_membership(user):
    return user.organisation_memberships.filter(is_admin=True).select_related("organisation").first()


def _admin_can_manage_organisation(user, organisation):
    membership = _clinic_admin_membership(user)
    return bool(membership and membership.organisation_id == organisation.id)


def _admin_can_manage_therapist(user, therapist):
    membership = _clinic_admin_membership(user)
    if not membership:
        return False

    return therapist.organisation_memberships.filter(
        organisation=membership.organisation,
    ).exists()


def _ensure_admin_can_be_removed(membership):
    if not membership.is_admin:
        return

    admin_count = OrganisationMember.objects.filter(
        organisation=membership.organisation,
        is_admin=True,
    ).count()
    member_count = OrganisationMember.objects.filter(
        organisation=membership.organisation,
    ).count()
    if admin_count <= 1 and member_count > 1:
        raise DjangoValidationError(
            {
                "is_admin": [
                    "No es pot deixar una organització amb membres sense cap administrador."
                ]
            }
        )


def _set_membership_admin(membership, is_admin):
    if membership.is_admin == is_admin:
        return membership

    if not is_admin:
        _ensure_admin_can_be_removed(membership)
        if OrganisationMember.objects.filter(organisation=membership.organisation).count() == 1:
            OrganisationMember.objects.filter(pk=membership.pk).update(is_admin=False)
            membership.refresh_from_db()
            return membership

    membership.is_admin = is_admin
    membership.save(update_fields=["is_admin"])
    return membership


@transaction.atomic
def _update_therapist_by_admin(*, therapist, attrs, allow_organisation_change):
    user_fields = []
    therapist_fields = []

    for field in ("first_name", "last_name", "email", "is_active"):
        if field in attrs and getattr(therapist, field) != attrs[field]:
            setattr(therapist, field, attrs[field])
            user_fields.append(field)

    for field in ("license_number", "specialty"):
        if field in attrs and getattr(therapist, field) != attrs[field]:
            setattr(therapist, field, attrs[field])
            therapist_fields.append(field)

    current_membership = therapist.organisation_memberships.select_related("organisation").first()

    if "organisation_id" in attrs:
        if not allow_organisation_change:
            raise DjangoValidationError(
                {"organisation_id": ["No pots moure terapeutes fora de la teva organització."]}
            )

        next_organisation = attrs["organisation_id"]
        next_organisation_id = next_organisation.id if next_organisation else None
        current_organisation_id = current_membership.organisation_id if current_membership else None

        if next_organisation_id != current_organisation_id:
            if current_membership:
                _ensure_admin_can_be_removed(current_membership)
                current_membership.delete()
                current_membership = None

            if next_organisation:
                current_membership = OrganisationMember.objects.create(
                    user=therapist,
                    organisation=next_organisation,
                    is_admin=attrs.get("is_admin", False),
                )
            elif attrs.get("is_admin"):
                raise DjangoValidationError(
                    {"is_admin": ["Un terapeuta independent no pot ser administrador de clínica."]}
                )

    if "is_admin" in attrs:
        is_admin = attrs["is_admin"]
        if current_membership is None:
            if is_admin:
                raise DjangoValidationError(
                    {"is_admin": ["Assigna una organització abans de marcar-lo com a administrador."]}
                )
        else:
            _set_membership_admin(current_membership, is_admin)

    if therapist_fields:
        therapist.save(update_fields=therapist_fields)
    if user_fields:
        therapist.save(update_fields=user_fields)

    return therapist


class OrganisationDetailView(APIView):
    permission_classes = [IsClinicAdminUser]

    @extend_schema(
        tags=["Users"],
        summary="Consultar una organització",
        responses={200: OrganisationSerializer},
    )
    def get(self, request, organisation_id):
        organisation = get_object_or_404(Organisation, pk=organisation_id)
        if not _admin_can_manage_organisation(request.user, organisation):
            return Response({"detail": "No tens permisos per gestionar aquesta organització."}, status=status.HTTP_403_FORBIDDEN)
        return Response(OrganisationSerializer(organisation).data)

    @extend_schema(
        tags=["Users"],
        summary="Modificar una organització",
        request=OrganisationUpdateSerializer,
        responses={200: OrganisationSerializer},
    )
    def patch(self, request, organisation_id):
        organisation = get_object_or_404(Organisation, pk=organisation_id)
        if not _admin_can_manage_organisation(request.user, organisation):
            return Response({"detail": "No tens permisos per gestionar aquesta organització."}, status=status.HTTP_403_FORBIDDEN)

        serializer = OrganisationUpdateSerializer(organisation, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        organisation = serializer.save()
        return Response(OrganisationSerializer(organisation).data)

    @extend_schema(
        tags=["Users"],
        summary="Eliminar una organització",
        responses={204: None},
    )
    def delete(self, request, organisation_id):
        organisation = get_object_or_404(Organisation, pk=organisation_id)
        if not _admin_can_manage_organisation(request.user, organisation):
            return Response({"detail": "No tens permisos per gestionar aquesta organització."}, status=status.HTTP_403_FORBIDDEN)

        organisation.is_active = False
        organisation.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class TherapistAdminDetailView(APIView):
    permission_classes = [IsClinicAdminUser]

    @extend_schema(
        tags=["Users"],
        summary="Consultar un terapeuta",
        responses={200: UserSummarySerializer},
    )
    def get(self, request, user_id):
        therapist = get_object_or_404(Therapist, pk=user_id)
        if not _admin_can_manage_therapist(request.user, therapist):
            return Response({"detail": "No tens permisos per gestionar aquest terapeuta."}, status=status.HTTP_403_FORBIDDEN)

        return Response(UserSummarySerializer(therapist).data)

    @extend_schema(
        tags=["Users"],
        summary="Modificar un terapeuta",
        request=TherapistAdminUpdateSerializer,
        responses={200: UserSummarySerializer},
    )
    def patch(self, request, user_id):
        therapist = get_object_or_404(Therapist, pk=user_id)
        if not _admin_can_manage_therapist(request.user, therapist):
            return Response({"detail": "No tens permisos per gestionar aquest terapeuta."}, status=status.HTTP_403_FORBIDDEN)

        serializer = TherapistAdminUpdateSerializer(
            data=request.data,
            partial=True,
            context={"therapist": therapist},
        )
        serializer.is_valid(raise_exception=True)

        try:
            therapist = _update_therapist_by_admin(
                therapist=therapist,
                attrs=serializer.validated_data,
                allow_organisation_change=False,
            )
        except DjangoValidationError as exc:
            return Response(_validation_detail(exc), status=status.HTTP_400_BAD_REQUEST)

        return Response(UserSummarySerializer(therapist).data)

    @extend_schema(
        tags=["Users"],
        summary="Eliminar un terapeuta",
        responses={204: None},
    )
    def delete(self, request, user_id):
        therapist = get_object_or_404(Therapist, pk=user_id)
        if not _admin_can_manage_therapist(request.user, therapist):
            return Response({"detail": "No tens permisos per gestionar aquest terapeuta."}, status=status.HTTP_403_FORBIDDEN)
        if request.user.pk == therapist.pk:
            return Response({"detail": "No pots eliminar el teu propi compte des de la gestió d'equip."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            delete_user_account(user=therapist)
            therapist.organisation_memberships.all().delete()
        except DjangoValidationError as exc:
            return Response(_validation_detail(exc), status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)


class ClinicTherapistListView(APIView):
    permission_classes = [IsClinicAdminUser]

    @extend_schema(
        tags=["Users"],
        summary="Llistar terapeutes de la clínica",
        responses={200: UserSummarySerializer(many=True)},
    )
    def get(self, request):
        membership = request.user.organisation_memberships.filter(is_admin=True).first()
        if not membership:
            return Response({"detail": "User is not an admin of any organisation."}, status=status.HTTP_403_FORBIDDEN)
        
        organisation = membership.organisation
        
        users = User.objects.filter(
            organisation_memberships__organisation=organisation, 
            role=User.Role.THERAPIST
        ).order_by("first_name", "last_name")
        return Response(UserSummarySerializer(users, many=True).data)
