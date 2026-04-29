from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.entries.models import JournalEntry, TherapistQuestion
from apps.entries.serializers import (
    JournalEntryDraftSerializer,
    JournalEntrySerializer,
    TherapistQuestionSerializer,
)
from apps.entries.services import soft_delete_entry
from apps.users.models import Patient
from apps.users.permissions import IsTherapistUser


class PatientEntriesMixin:
    permission_classes = [IsAuthenticated]

    def get_patient(self, request):
        return getattr(request.user, "patient_profile", None)

    def ensure_patient(self, request):
        patient = self.get_patient(request)
        if patient is None:
            return None, Response(
                {"detail": "Only patients can manage journal entries."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return patient, None

    def get_entry(self, *, patient, entry_id):
        return (
            JournalEntry.objects.select_related("therapist_question")
            .filter(pk=entry_id, patient=patient)
            .first()
        )


class JournalEditorContextView(PatientEntriesMixin, APIView):
    @extend_schema(
        tags=["entries"],
        summary="Obtenir context de l’editor de journaling",
        responses={
            200: inline_serializer(
                name="JournalEditorContextResponse",
                fields={
                    "active_question": TherapistQuestionSerializer(allow_null=True),
                },
            ),
            403: OpenApiResponse(description="Només els pacients poden gestionar entrades."),
        },
    )
    def get(self, request):
        patient, error_response = self.ensure_patient(request)
        if error_response is not None:
            return error_response

        active_question = (
            TherapistQuestion.objects.filter(patient=patient, is_active=True)
            .select_related("therapist", "patient")
            .first()
        )
        return Response(
            {
                "active_question": TherapistQuestionSerializer(active_question).data if active_question else None,
            },
            status=status.HTTP_200_OK,
        )


class JournalEntryListCreateView(PatientEntriesMixin, APIView):
    @extend_schema(
        tags=["entries"],
        summary="Llistar entrades",
        responses={
            200: JournalEntrySerializer(many=True),
            403: OpenApiResponse(description="Només els pacients poden gestionar entrades."),
        },
    )
    def get(self, request):
        patient, error_response = self.ensure_patient(request)
        if error_response is not None:
            return error_response

        entries = (
            JournalEntry.objects.filter(patient=patient)
            .select_related("therapist_question")
            .order_by("-updated_at")
        )
        return Response(JournalEntrySerializer(entries, many=True).data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["entries"],
        summary="Crear esborrany d’entrada",
        request=JournalEntryDraftSerializer,
        responses={
            201: JournalEntrySerializer,
            400: OpenApiResponse(description="L’entrada no pot estar buida."),
            403: OpenApiResponse(description="Només els pacients poden gestionar entrades."),
        },
        examples=[
            OpenApiExample(
                "Crear esborrany",
                value={"content": "Avui m’he sentit amb més claredat després de parlar amb la meva germana."},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        patient, error_response = self.ensure_patient(request)
        if error_response is not None:
            return error_response

        serializer = JournalEntryDraftSerializer(data=request.data, context={"patient": patient})
        serializer.is_valid(raise_exception=True)
        entry = serializer.save()
        return Response(JournalEntrySerializer(entry).data, status=status.HTTP_201_CREATED)


class JournalEntryDetailView(PatientEntriesMixin, APIView):
    @extend_schema(
        tags=["entries"],
        summary="Obtenir una entrada",
        responses={
            200: JournalEntrySerializer,
            403: OpenApiResponse(description="Només els pacients poden gestionar entrades."),
            404: OpenApiResponse(description="Entrada no trobada."),
        },
    )
    def get(self, request, entry_id):
        patient, error_response = self.ensure_patient(request)
        if error_response is not None:
            return error_response

        entry = self.get_entry(patient=patient, entry_id=entry_id)
        if entry is None:
            return Response({"detail": "Entry not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(JournalEntrySerializer(entry).data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["entries"],
        summary="Actualitzar esborrany d’entrada",
        request=JournalEntryDraftSerializer,
        responses={
            200: JournalEntrySerializer,
            400: OpenApiResponse(description="L’entrada no pot estar buida o l’entrada està eliminada."),
            403: OpenApiResponse(description="Només els pacients poden gestionar entrades."),
            404: OpenApiResponse(description="Entrada no trobada."),
        },
    )
    def patch(self, request, entry_id):
        patient, error_response = self.ensure_patient(request)
        if error_response is not None:
            return error_response

        entry = self.get_entry(patient=patient, entry_id=entry_id)
        if entry is None:
            return Response({"detail": "Entry not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = JournalEntryDraftSerializer(
            entry,
            data=request.data,
            partial=True,
            context={"patient": patient},
        )
        serializer.is_valid(raise_exception=True)
        updated_entry = serializer.save()
        return Response(JournalEntrySerializer(updated_entry).data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["entries"],
        summary="Eliminar lògicament una entrada",
        responses={
            200: inline_serializer(
                name="JournalEntryDeleteResponse",
                fields={
                    "message": serializers.CharField(),
                    "entry": JournalEntrySerializer(),
                },
            ),
            403: OpenApiResponse(description="Només els pacients poden gestionar entrades."),
            404: OpenApiResponse(description="Entrada no trobada."),
        },
    )
    def delete(self, request, entry_id):
        patient, error_response = self.ensure_patient(request)
        if error_response is not None:
            return error_response

        entry = self.get_entry(patient=patient, entry_id=entry_id)
        if entry is None:
            return Response({"detail": "Entry not found."}, status=status.HTTP_404_NOT_FOUND)

        entry = soft_delete_entry(entry=entry)
        return Response(
            {
                "message": "Entrada eliminada i anonimitzada correctament.",
                "entry": JournalEntrySerializer(entry).data,
            },
            status=status.HTTP_200_OK,
        )

class TherapistPatientMixin:
    permission_classes = [IsTherapistUser]

    def get_patient(self, request, patient_id):
        therapist = request.user.therapist_profile
        return get_object_or_404(
            Patient,
            pk=patient_id,
            therapist_links__therapist=therapist
        )


class TherapistPatientEntriesView(TherapistPatientMixin, APIView):
    @extend_schema(
        tags=["therapist-patients"],
        summary="Llistar entrades d'un pacient (Terapeuta)",
        responses={
            200: JournalEntrySerializer(many=True),
            403: OpenApiResponse(description="Només els terapeutes poden accedir a aquesta informació."),
            404: OpenApiResponse(description="Pacient no trobat o no assignat."),
        },
    )
    def get(self, request, patient_id):
        patient = self.get_patient(request, patient_id)
        entries = JournalEntry.objects.filter(patient=patient).select_related("therapist_question").order_by("-updated_at")
        return Response(JournalEntrySerializer(entries, many=True).data, status=status.HTTP_200_OK)


class TherapistPatientEntryDetailView(TherapistPatientMixin, APIView):
    @extend_schema(
        tags=["therapist-patients"],
        summary="Obtenir detall d'una entrada d'un pacient (Terapeuta)",
        responses={
            200: JournalEntrySerializer,
            403: OpenApiResponse(description="Només els terapeutes poden accedir a aquesta informació."),
            404: OpenApiResponse(description="Entrada o pacient no trobats."),
        },
    )
    def get(self, request, patient_id, entry_id):
        patient = self.get_patient(request, patient_id)
        entry = get_object_or_404(JournalEntry, pk=entry_id, patient=patient)
        return Response(JournalEntrySerializer(entry).data, status=status.HTTP_200_OK)


class TherapistPatientQuestionsView(TherapistPatientMixin, APIView):
    @extend_schema(
        tags=["therapist-patients"],
        summary="Llistar preguntes d'un pacient (Terapeuta)",
        responses={
            200: TherapistQuestionSerializer(many=True),
            403: OpenApiResponse(description="Només els terapeutes poden accedir a aquesta informació."),
            404: OpenApiResponse(description="Pacient no trobat o no assignat."),
        },
    )
    def get(self, request, patient_id):
        patient = self.get_patient(request, patient_id)
        questions = TherapistQuestion.objects.filter(patient=patient).order_by("-created_at")
        return Response(TherapistQuestionSerializer(questions, many=True).data, status=status.HTTP_200_OK)


class TherapistPatientQuestionDetailView(TherapistPatientMixin, APIView):
    @extend_schema(
        tags=["therapist-patients"],
        summary="Obtenir detall d'una pregunta d'un pacient (Terapeuta)",
        responses={
            200: TherapistQuestionSerializer,
            403: OpenApiResponse(description="Només els terapeutes poden accedir a aquesta informació."),
            404: OpenApiResponse(description="Pregunta o pacient no trobats."),
        },
    )
    def get(self, request, patient_id, question_id):
        patient = self.get_patient(request, patient_id)
        question = get_object_or_404(TherapistQuestion, pk=question_id, patient=patient)
        return Response(TherapistQuestionSerializer(question).data, status=status.HTTP_200_OK)
