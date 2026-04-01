from pathlib import Path

from django.http import FileResponse, Http404
from rest_framework import status
from django.conf import settings
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsTherapistUser
from apps.users.serializers import (
    ChangePasswordSerializer,
    DeleteAccountSerializer,
    LoginSerializer,
    PasswordForgotSerializer,
    PasswordResetSerializer,
    PatientConsentAcceptSerializer,
    PatientConsentRejectSerializer,
    PatientActivationSerializer,
    PatientRegistrationSerializer,
    RefreshTokenSerializer,
    ProfileUpdateSerializer,
    TherapistRegistrationSerializer,
    TherapistPatientDeactivateSerializer,
    TwoFactorDisableSerializer,
    TwoFactorEnableSerializer,
    TwoFactorSetupSerializer,
    TwoFactorVerifySerializer,
    UserSummarySerializer,
)


class TherapistRegistrationView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = TherapistRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        therapist = serializer.save()

        response_serializer = TherapistRegistrationSerializer(therapist)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class PatientRegistrationView(APIView):
    permission_classes = [IsTherapistUser]

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


class PatientActivationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PatientActivationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        patient = serializer.save()

        return Response(
            {
                "id": str(patient.pk),
                "email": patient.email,
                "is_active": patient.is_active,
                "message": "Patient account activated successfully.",
            },
            status=status.HTTP_200_OK,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

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

    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.blacklist()
        return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)


class PasswordForgotView(APIView):
    permission_classes = [AllowAny]

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

    def get(self, request):
        return Response(UserSummarySerializer(request.user).data, status=status.HTTP_200_OK)

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


class PatientConsentAcceptView(APIView):
    permission_classes = [IsAuthenticated]

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

    def post(self, request):
        serializer = TwoFactorSetupSerializer(context={"user": request.user})
        setup_data = serializer.save()
        return Response(setup_data, status=status.HTTP_200_OK)


class TwoFactorEnableView(APIView):
    permission_classes = [IsAuthenticated]

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

    def get(self, request):
        pdf_path = Path(__file__).resolve().parent / "data" / "Reflexia_ Consentiment Informat.pdf"
        if not pdf_path.exists():
            raise Http404("Consent document not found.")

        return FileResponse(
            pdf_path.open("rb"),
            content_type="application/pdf",
            filename="Reflexia_Consentiment_Informat.pdf",
        )
