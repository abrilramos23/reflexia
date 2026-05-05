from pathlib import Path
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404
from rest_framework import status
from django.conf import settings
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, inline_serializer
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers

from apps.users.permissions import IsTherapistUser, IsPlatformAdminUser, IsClinicAdminUser
from apps.users.models import User, Patient, Therapist, Organisation
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
    OrganisationCreateSerializer,
    ClinicAdminRegistrationSerializer,
)


class TherapistRegistrationView(APIView):
    permission_classes = [IsPlatformAdminUser | IsClinicAdminUser]

    @extend_schema(
        tags=["auth"],
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
                    "specialty": "Clinical Psychology",
                    "organisation_id": "11111111-1111-1111-1111-111111111111",
                    "is_admin": True,
                },
                request_only=True,
            )
        ],
    )
    def post(self, request):
        context = {}
        if request.user.is_clinic_admin:
            membership = request.user.organisation_memberships.filter(is_admin=True).first()
            if membership:
                context["organisation"] = membership.organisation
        # If PlatformAdmin, the organisation_id is handled inside the serializer's create method
        # via the request data.

        serializer = TherapistRegistrationSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        therapist = serializer.save()

        response_serializer = TherapistRegistrationSerializer(therapist)
        response_data = {
            **response_serializer.data,
            "is_clinic_admin": therapist.is_clinic_admin,
            "activation_email_sent": True,
        }
        if settings.DEBUG:
            response_data["activation_url"] = serializer.context.get("activation_url")
        return Response(response_data, status=status.HTTP_201_CREATED)


class PatientRegistrationView(APIView):
    permission_classes = [IsTherapistUser]

    @extend_schema(
        tags=["auth"],
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
        tags=["auth"],
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
        tags=["auth"],
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
        tags=["auth"],
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
        tags=["auth"],
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
        tags=["auth"],
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
        tags=["profile"],
        summary="Obtenir usuari autenticat",
        responses={200: UserSummarySerializer},
    )
    def get(self, request):
        return Response(UserSummarySerializer(request.user).data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["profile"],
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
        tags=["profile"],
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
        tags=["profile"],
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
        tags=["profile"],
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
        tags=["profile"],
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
        tags=["profile"],
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


class PatientConsentAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["profile"],
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
        tags=["profile"],
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
        tags=["2fa"],
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
        tags=["2fa"],
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
        tags=["2fa"],
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
        tags=["2fa"],
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
        tags=["documents"],
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
class PlatformStatsView(APIView):
    permission_classes = [IsPlatformAdminUser]

    @extend_schema(
        tags=["admin"],
        summary="Obtenir estadístiques de la plataforma",
        responses={200: inline_serializer(
            name="PlatformStats",
            fields={
                "total_organisations": serializers.IntegerField(),
                "total_users": serializers.IntegerField(),
                "total_clinic_admins": serializers.IntegerField(),
                "users_by_role": serializers.DictField(),
            }
        )}
    )
    def get(self, request):
        stats = {
            "total_organisations": Organisation.objects.count(),
            "total_users": User.objects.count(),
            "total_clinic_admins": User.objects.filter(
                organisation_memberships__is_admin=True
            ).distinct().count(),
            "users_by_role": {
                role: User.objects.filter(role=role).count()
                for role, _ in User.Role.choices
            }
        }
        return Response(stats)


class ClinicStatsView(APIView):
    permission_classes = [IsClinicAdminUser]

    @extend_schema(
        tags=["admin"],
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


class OrganisationListCreateView(APIView):
    permission_classes = [IsPlatformAdminUser]

    @extend_schema(
        tags=["admin"],
        summary="Llistar i crear organitzacions",
        request=OrganisationCreateSerializer,
        responses={
            200: OrganisationSerializer(many=True),
            201: OrganisationSerializer,
        },
    )
    def get(self, request):
        organisations = Organisation.objects.all().order_by("name")
        return Response(OrganisationSerializer(organisations, many=True).data)

    def post(self, request):
        serializer = OrganisationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organisation = serializer.save()
        return Response(OrganisationSerializer(organisation).data, status=status.HTTP_201_CREATED)


class ClinicAdminRegistrationView(APIView):
    permission_classes = [IsPlatformAdminUser]

    @extend_schema(
        tags=["admin"],
        summary="Registrar un administrador de clínica",
        request=ClinicAdminRegistrationSerializer,
        responses={
            201: inline_serializer(
                name="ClinicAdminRegistrationResponse",
                fields={
                    "id": serializers.UUIDField(),
                    "first_name": serializers.CharField(),
                    "last_name": serializers.CharField(),
                    "email": serializers.EmailField(),
                    "license_number": serializers.CharField(),
                    "specialty": serializers.CharField(),
                    "is_clinic_admin": serializers.BooleanField(),
                    "organisation": OrganisationSerializer(),
                },
            ),
        },
        examples=[
            OpenApiExample(
                "Assignar terapeuta existent com a admin de clínica",
                value={
                    "organisation_id": "11111111-1111-1111-1111-111111111111",
                    "therapist_id": "22222222-2222-2222-2222-222222222222",
                },
                request_only=True,
            )
        ],
    )
    def post(self, request):
        serializer = ClinicAdminRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        therapist = serializer.save()

        response_data = {
            "id": therapist.id,
            "first_name": therapist.first_name,
            "last_name": therapist.last_name,
            "email": therapist.email,
            "license_number": therapist.license_number,
            "specialty": therapist.specialty,
            "is_clinic_admin": therapist.is_clinic_admin,
            "organisation": OrganisationSerializer(therapist.organisation).data if therapist.organisation else None,
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


class GlobalClinicAdminListView(APIView):
    permission_classes = [IsPlatformAdminUser]

    @extend_schema(
        tags=["admin"],
        summary="Llistar tots els administradors de clínica",
        responses={200: UserSummarySerializer(many=True)},
    )
    def get(self, request):
        users = User.objects.filter(
            organisation_memberships__is_admin=True
        ).distinct().order_by("first_name", "last_name")
        return Response(UserSummarySerializer(users, many=True).data)


class GlobalTherapistListView(APIView):
    permission_classes = [IsPlatformAdminUser]

    @extend_schema(
        tags=["admin"],
        summary="Llistar tots els terapeutes globals",
        responses={200: UserSummarySerializer(many=True)},
    )
    def get(self, request):
        users = User.objects.filter(role=User.Role.THERAPIST).order_by("first_name", "last_name")
        return Response(UserSummarySerializer(users, many=True).data)


class ClinicTherapistListView(APIView):
    permission_classes = [IsClinicAdminUser]

    @extend_schema(
        tags=["admin"],
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
