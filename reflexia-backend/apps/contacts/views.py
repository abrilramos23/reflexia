from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import status
from rest_framework import serializers
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
from apps.users.models import Therapist
from apps.users.permissions import IsTherapistUser


class AssociatedContactListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["contacts"],
        summary="Llistar contactes associats",
        responses={
            200: AssociatedContactSerializer(many=True),
            403: OpenApiResponse(description="Només els pacients poden gestionar contactes associats."),
        },
    )
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

    @extend_schema(
        tags=["contacts"],
        summary="Crear contacte associat",
        request=AssociatedContactSerializer,
        responses={
            201: AssociatedContactSerializer,
            400: OpenApiResponse(description="Cal informar com a mínim correu o telèfon."),
            403: OpenApiResponse(description="Només els pacients poden gestionar contactes associats."),
        },
        examples=[
            OpenApiExample(
                "Nou contacte associat",
                value={
                    "name": "Maria Perez",
                    "relation": "Germana",
                    "email": "maria@example.com",
                    "phone": "",
                    "is_default": True,
                },
                request_only=True,
            )
        ],
    )
    def post(self, request):
        if not hasattr(request.user, "patient_profile"):
            return Response({"detail": "Only patients can manage associated contacts."}, status=status.HTTP_403_FORBIDDEN)

        serializer = AssociatedContactSerializer(data=request.data, context={"patient": request.user.patient_profile})
        serializer.is_valid(raise_exception=True)
        contact = serializer.save()
        return Response(
            AssociatedContactSerializer(contact, context={"patient": request.user.patient_profile}).data,
            status=status.HTTP_201_CREATED,
        )


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

    @extend_schema(
        tags=["contacts"],
        summary="Actualitzar contacte associat",
        parameters=[
            OpenApiParameter(
                name="contact_id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description="Identificador del contacte associat.",
            )
        ],
        request=AssociatedContactSerializer,
        responses={
            200: AssociatedContactSerializer,
            403: OpenApiResponse(description="Només els pacients poden gestionar contactes associats."),
            404: OpenApiResponse(description="Contacte no trobat."),
        },
    )
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

    @extend_schema(
        tags=["contacts"],
        summary="Eliminar contacte associat",
        parameters=[
            OpenApiParameter(
                name="contact_id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description="Identificador del contacte associat.",
            )
        ],
        responses={
            200: inline_serializer(
                name="AssociatedContactDeleteResponse",
                fields={"message": serializers.CharField()},
            ),
            403: OpenApiResponse(description="Només els pacients poden gestionar contactes associats."),
            404: OpenApiResponse(description="Contacte no trobat."),
        },
    )
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

    @extend_schema(
        tags=["contacts"],
        summary="Llistar terapeutes de suport",
        responses={
            200: SupportTherapistListSerializer(many=True),
            403: OpenApiResponse(description="Només els terapeutes poden gestionar terapeutes de suport."),
        },
    )
    def get(self, request):
        therapist = request.user.therapist_profile
        if not therapist.organisation_memberships.filter(organisation__type='clinic').exists():
            return Response([], status=status.HTTP_200_OK)

        links = SupportTherapist.objects.filter(therapist=therapist).select_related("support")
        return Response(SupportTherapistListSerializer(links, many=True).data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["contacts"],
        summary="Afegir terapeuta de suport",
        request=SupportTherapistCreateSerializer,
        responses={
            201: SupportTherapistListSerializer,
            400: OpenApiResponse(description="El terapeuta de suport no existeix, ja està assignat o coincideix amb el terapeuta autenticat."),
            403: OpenApiResponse(description="Només els terapeutes poden gestionar terapeutes de suport."),
        },
        examples=[
            OpenApiExample(
                "Afegir terapeuta de suport",
                value={"support_id": "11111111-1111-1111-1111-111111111111"},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        serializer = SupportTherapistCreateSerializer(data=request.data, context={"therapist": request.user.therapist_profile})
        serializer.is_valid(raise_exception=True)
        link = serializer.save()
        return Response(SupportTherapistListSerializer(link).data, status=status.HTTP_201_CREATED)


class SupportTherapistDeleteView(APIView):
    permission_classes = [IsTherapistUser]

    @extend_schema(
        tags=["contacts"],
        summary="Eliminar terapeuta de suport",
        parameters=[
            OpenApiParameter(
                name="support_id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description="Identificador del terapeuta de suport a eliminar.",
            )
        ],
        responses={
            200: inline_serializer(
                name="SupportTherapistDeleteResponse",
                fields={"message": serializers.CharField()},
            ),
            404: OpenApiResponse(description="Terapeuta de suport no trobat."),
        },
    )
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

    @extend_schema(
        tags=["contacts"],
        summary="Llistar terapeutes disponibles com a suport",
        responses={
            200: AvailableTherapistSerializer(many=True),
            403: OpenApiResponse(description="Només els terapeutes poden gestionar terapeutes de suport."),
        },
    )
    def get(self, request):
        therapist = request.user.therapist_profile
        if not therapist.organisation_memberships.filter(organisation__type='clinic').exists():
            return Response([], status=status.HTTP_200_OK)

        assigned_ids = SupportTherapist.objects.filter(therapist=therapist).values_list("support_id", flat=True)
        therapists = Therapist.objects.exclude(pk=therapist.pk).exclude(pk__in=assigned_ids)
        return Response(AvailableTherapistSerializer(therapists, many=True).data, status=status.HTTP_200_OK)
