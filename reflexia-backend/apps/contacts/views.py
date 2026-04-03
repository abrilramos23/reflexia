from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.contacts.models import AssociatedContact, DefaultContact, SupportTherapist
from apps.contacts.serializers import (
    AssociatedContactSerializer,
    AvailableTherapistSerializer,
    SupportTherapistCreateSerializer,
    SupportTherapistListSerializer,
)
from apps.users.permissions import IsTherapistUser


class AssociatedContactListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["contacts"], summary="List associated contacts")
    def get(self, request):
        if not hasattr(request.user, "patient_profile"):
            return Response({"detail": "Only patients can manage associated contacts."}, status=status.HTTP_403_FORBIDDEN)

        patient = request.user.patient_profile
        links = DefaultContact.objects.filter(patient=patient).select_related("contact").order_by("-is_default", "contact__name")

        contacts = []
        for link in links:
            contact = link.contact
            contact._patient_link = link
            contacts.append(contact)

        serializer = AssociatedContactSerializer(contacts, many=True, context={"patient": patient})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(tags=["contacts"], summary="Create associated contact", request=AssociatedContactSerializer, responses={201: AssociatedContactSerializer})
    def post(self, request):
        if not hasattr(request.user, "patient_profile"):
            return Response({"detail": "Only patients can manage associated contacts."}, status=status.HTTP_403_FORBIDDEN)

        serializer = AssociatedContactSerializer(data=request.data, context={"patient": request.user.patient_profile})
        serializer.is_valid(raise_exception=True)
        contact = serializer.save()
        return Response(AssociatedContactSerializer(contact).data, status=status.HTTP_201_CREATED)


class AssociatedContactDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, contact_id):
        patient = request.user.patient_profile
        contact = AssociatedContact.objects.filter(
            pk=contact_id,
        ).first()
        if contact is None:
            return None

        link = DefaultContact.objects.filter(patient=patient, contact=contact).first()
        if link is None:
            return None

        contact._patient_link = link
        return contact

    @extend_schema(tags=["contacts"], summary="Update associated contact", request=AssociatedContactSerializer, responses={200: AssociatedContactSerializer})
    def patch(self, request, contact_id):
        if not hasattr(request.user, "patient_profile"):
            return Response({"detail": "Only patients can manage associated contacts."}, status=status.HTTP_403_FORBIDDEN)

        contact = self.get_object(request, contact_id)
        if contact is None:
            return Response({"detail": "Contact not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AssociatedContactSerializer(
            contact,
            data=request.data,
            partial=True,
            context={"patient": request.user.patient_profile},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(tags=["contacts"], summary="Delete associated contact", responses={200: None})
    def delete(self, request, contact_id):
        if not hasattr(request.user, "patient_profile"):
            return Response({"detail": "Only patients can manage associated contacts."}, status=status.HTTP_403_FORBIDDEN)

        contact = self.get_object(request, contact_id)
        if contact is None:
            return Response({"detail": "Contact not found."}, status=status.HTTP_404_NOT_FOUND)

        deleted_links, _ = DefaultContact.objects.filter(
            patient=request.user.patient_profile,
            contact=contact,
        ).delete()

        if deleted_links and not DefaultContact.objects.filter(contact=contact).exists():
            contact.delete()

        return Response({"message": "Associated contact deleted successfully."}, status=status.HTTP_200_OK)


class SupportTherapistListCreateView(APIView):
    permission_classes = [IsTherapistUser]

    @extend_schema(tags=["contacts"], summary="List support therapists")
    def get(self, request):
        links = SupportTherapist.objects.filter(therapist=request.user.therapist_profile).select_related("support")
        return Response(SupportTherapistListSerializer(links, many=True).data, status=status.HTTP_200_OK)

    @extend_schema(tags=["contacts"], summary="Add support therapist", request=SupportTherapistCreateSerializer, responses={201: SupportTherapistListSerializer})
    def post(self, request):
        serializer = SupportTherapistCreateSerializer(data=request.data, context={"therapist": request.user.therapist_profile})
        serializer.is_valid(raise_exception=True)
        link = serializer.save()
        return Response(SupportTherapistListSerializer(link).data, status=status.HTTP_201_CREATED)


class SupportTherapistDeleteView(APIView):
    permission_classes = [IsTherapistUser]

    @extend_schema(tags=["contacts"], summary="Delete support therapist", responses={200: None})
    def delete(self, request, support_id):
        deleted, _ = SupportTherapist.objects.filter(
            therapist=request.user.therapist_profile,
            support_id=support_id,
        ).delete()

        if not deleted:
            return Response({"detail": "Support therapist not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"message": "Support therapist deleted successfully."}, status=status.HTTP_200_OK)


class AvailableSupportTherapistListView(APIView):
    permission_classes = [IsTherapistUser]

    @extend_schema(tags=["contacts"], summary="List available therapists for support assignment")
    def get(self, request):
        therapist = request.user.therapist_profile
        assigned_ids = SupportTherapist.objects.filter(therapist=therapist).values_list("support_id", flat=True)
        therapists = Therapist.objects.exclude(pk=therapist.pk).exclude(pk__in=assigned_ids)
        return Response(AvailableTherapistSerializer(therapists, many=True).data, status=status.HTTP_200_OK)
