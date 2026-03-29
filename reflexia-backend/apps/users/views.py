from rest_framework import status
from django.conf import settings
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsTherapistUser
from apps.users.serializers import (
    PatientActivationSerializer,
    PatientRegistrationSerializer,
    TherapistRegistrationSerializer,
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
