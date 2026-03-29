from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers import TherapistRegistrationSerializer


class TherapistRegistrationView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = TherapistRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        therapist = serializer.save()

        response_serializer = TherapistRegistrationSerializer(therapist)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
