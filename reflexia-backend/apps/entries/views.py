from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analysis.models import EmotionalAnalysis
from apps.analysis.serializers import EmotionalAnalysisSerializer
from apps.analysis.services import AnalysisServiceError, analyze_journal_entry
from apps.entries.models import JournalEntry, PrivateNote, TherapistQuestion
from apps.entries.serializers import (
    JournalEntryDraftSerializer,
    JournalEntrySerializer,
    PrivateNoteCreateSerializer,
    PrivateNoteSerializer,
    TherapistQuestionCreateSerializer,
    TherapistQuestionSerializer,
)
from apps.entries.services import (
    ENTRY_DELETION_EXPLANATION,
    build_export_filename,
    render_entries_pdf,
    soft_delete_entry,
)
from apps.users.models import Patient
from apps.users.permissions import IsTherapistUser


VISIBLE_ENTRY_STATUSES = [JournalEntry.STATUS_ACTIVE, JournalEntry.STATUS_MODIFIED]


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

    def get_visible_entries_queryset(self, *, patient):
        return (
            JournalEntry.objects.filter(patient=patient, status__in=VISIBLE_ENTRY_STATUSES)
            .select_related("therapist_question", "analysis")
            .order_by("-updated_at")
        )

    def get_visible_entry(self, *, patient, entry_id):
        return self.get_visible_entries_queryset(patient=patient).filter(pk=entry_id).first()


class TherapistPatientMixin:
    permission_classes = [IsTherapistUser]

    def get_patient(self, request, patient_id):
        therapist = request.user.therapist_profile
        return get_object_or_404(
            Patient,
            pk=patient_id,
            therapist_links__therapist=therapist,
            therapist_links__is_active=True,
        )

    def get_visible_entries_queryset(self, *, patient):
        return (
            JournalEntry.objects.filter(patient=patient, status__in=VISIBLE_ENTRY_STATUSES)
            .select_related("therapist_question", "analysis")
            .order_by("-updated_at")
        )


class JournalEditorContextView(PatientEntriesMixin, APIView):
    @extend_schema(
        tags=["Entries"],
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
        tags=["Entries"],
        summary="Llistar entrades visibles del pacient",
        responses={
            200: JournalEntrySerializer(many=True),
            403: OpenApiResponse(description="Només els pacients poden gestionar entrades."),
        },
    )
    def get(self, request):
        patient, error_response = self.ensure_patient(request)
        if error_response is not None:
            return error_response

        entries = self.get_visible_entries_queryset(patient=patient)
        return Response(JournalEntrySerializer(entries, many=True).data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Entries"],
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
        tags=["Entries"],
        summary="Obtenir una entrada visible",
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

        entry = self.get_visible_entry(patient=patient, entry_id=entry_id)
        if entry is None:
            return Response({"detail": "Entrada no trobada."}, status=status.HTTP_404_NOT_FOUND)

        return Response(JournalEntrySerializer(entry).data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Entries"],
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

        entry = self.get_visible_entry(patient=patient, entry_id=entry_id)
        if entry is None:
            return Response({"detail": "Entrada no trobada."}, status=status.HTTP_404_NOT_FOUND)

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
        tags=["Entries"],
        summary="Eliminar lògicament una entrada",
        responses={
            200: inline_serializer(
                name="JournalEntryDeleteResponse",
                fields={
                    "message": serializers.CharField(),
                    "retention_explanation": serializers.CharField(),
                    "retention_date": serializers.DateTimeField(),
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

        entry = self.get_visible_entry(patient=patient, entry_id=entry_id)
        if entry is None:
            return Response({"detail": "Entrada no trobada."}, status=status.HTTP_404_NOT_FOUND)

        entry = soft_delete_entry(entry=entry)
        return Response(
            {
                "message": "Entrada eliminada de l’historial visible. Les dades s’han conservat anonimitzades.",
                "retention_explanation": ENTRY_DELETION_EXPLANATION,
                "retention_date": entry.retention_date,
            },
            status=status.HTTP_200_OK,
        )


class PatientAnalyzeEntryView(PatientEntriesMixin, APIView):
    @extend_schema(
        tags=["Entries"],
        summary="Generar anàlisi emocional d'una entrada visible",
        responses={
            200: inline_serializer(
                name="PatientAnalyzeEntryResponse",
                fields={
                    "message": serializers.CharField(),
                    "entry": JournalEntrySerializer(),
                },
            ),
            403: OpenApiResponse(description="Només els pacients poden analitzar entrades pròpies."),
            404: OpenApiResponse(description="Entrada no trobada."),
            503: OpenApiResponse(description="Servei d'anàlisi no disponible."),
        },
    )
    def post(self, request, entry_id):
        patient, error_response = self.ensure_patient(request)
        if error_response is not None:
            return error_response

        entry = self.get_visible_entry(patient=patient, entry_id=entry_id)
        if entry is None:
            return Response({"detail": "Entrada no trobada."}, status=status.HTTP_404_NOT_FOUND)

        try:
            analyze_journal_entry(entry=entry)
        except AnalysisServiceError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        entry.refresh_from_db()
        return Response(
            {
                "message": "Anàlisi generada correctament. Recorda que és orientativa i serà revisada pel terapeuta.",
                "entry": JournalEntrySerializer(entry).data,
            },
            status=status.HTTP_200_OK,
        )


class PatientEntryExportView(PatientEntriesMixin, APIView):
    @extend_schema(
        tags=["Entries"],
        summary="Exportar una entrada del pacient a PDF",
        operation_id="entries_export_entry",
        responses={200: OpenApiResponse(description="PDF generat correctament.")},
    )
    def get(self, request, entry_id):
        patient, error_response = self.ensure_patient(request)
        if error_response is not None:
            return error_response

        entry = self.get_visible_entry(patient=patient, entry_id=entry_id)
        if entry is None:
            return Response({"detail": "Entrada no trobada."}, status=status.HTTP_404_NOT_FOUND)

        pdf_bytes = render_entries_pdf(title="Exportació d'una entrada de journaling", entries=[entry])
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{build_export_filename(prefix="entry", suffix=str(entry.pk)[:8])}"'
        return response


class PatientEntriesExportView(PatientEntriesMixin, APIView):
    @extend_schema(
        tags=["Entries"],
        summary="Exportar l'historial del pacient a PDF",
        operation_id="entries_export_history",
        responses={200: OpenApiResponse(description="PDF generat correctament.")},
    )
    def get(self, request):
        patient, error_response = self.ensure_patient(request)
        if error_response is not None:
            return error_response

        entries = list(self.get_visible_entries_queryset(patient=patient))
        pdf_bytes = render_entries_pdf(title="Historial de journaling", entries=entries)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{build_export_filename(prefix="entries-history")}"'
        return response


class TherapistPatientEntriesView(TherapistPatientMixin, APIView):
    @extend_schema(
        tags=["Entries"],
        summary="Llistar entrades visibles d'un pacient (Terapeuta)",
        responses={
            200: JournalEntrySerializer(many=True),
            403: OpenApiResponse(description="Només els terapeutes poden accedir a aquesta informació."),
            404: OpenApiResponse(description="Pacient no trobat o no assignat."),
        },
    )
    def get(self, request, patient_id):
        patient = self.get_patient(request, patient_id)
        entries = self.get_visible_entries_queryset(patient=patient)
        return Response(JournalEntrySerializer(entries, many=True).data, status=status.HTTP_200_OK)


class TherapistPatientEntryDetailView(TherapistPatientMixin, APIView):
    @extend_schema(
        tags=["Entries"],
        summary="Obtenir detall d'una entrada visible d'un pacient (Terapeuta)",
        responses={
            200: JournalEntrySerializer,
            403: OpenApiResponse(description="Només els terapeutes poden accedir a aquesta informació."),
            404: OpenApiResponse(description="Entrada o pacient no trobats."),
        },
    )
    def get(self, request, patient_id, entry_id):
        patient = self.get_patient(request, patient_id)
        entry = get_object_or_404(self.get_visible_entries_queryset(patient=patient), pk=entry_id)
        return Response(JournalEntrySerializer(entry).data, status=status.HTTP_200_OK)


class TherapistPatientEntryNotesView(TherapistPatientMixin, APIView):
    @extend_schema(
        tags=["Entries"],
        summary="Llistar notes privades d'una entrada",
        responses={
            200: PrivateNoteSerializer(many=True),
            404: OpenApiResponse(description="Pacient o entrada no trobats."),
        },
    )
    def get(self, request, patient_id, entry_id):
        patient = self.get_patient(request, patient_id)
        entry = get_object_or_404(self.get_visible_entries_queryset(patient=patient), pk=entry_id)
        therapist = request.user.therapist_profile
        notes = PrivateNote.objects.filter(entry=entry, therapist=therapist).order_by("-creation_date")
        return Response(PrivateNoteSerializer(notes, many=True).data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Entries"],
        summary="Afegir una nota privada a una entrada",
        request=PrivateNoteCreateSerializer,
        responses={
            201: inline_serializer(
                name="PrivateNoteCreateResponse",
                fields={
                    "message": serializers.CharField(),
                    "note": PrivateNoteSerializer(),
                },
            ),
            404: OpenApiResponse(description="Pacient o entrada no trobats."),
        },
    )
    def post(self, request, patient_id, entry_id):
        patient = self.get_patient(request, patient_id)
        entry = get_object_or_404(self.get_visible_entries_queryset(patient=patient), pk=entry_id)
        therapist = request.user.therapist_profile
        serializer = PrivateNoteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note = serializer.save(entry=entry, therapist=therapist)
        return Response(
            {
                "message": "Nota privada guardada correctament.",
                "note": PrivateNoteSerializer(note).data,
            },
            status=status.HTTP_201_CREATED,
        )


class TherapistPatientQuestionsView(TherapistPatientMixin, APIView):
    @extend_schema(
        tags=["Entries"],
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

    @extend_schema(
        tags=["Entries"],
        summary="Crear una pregunta per a un pacient (Terapeuta)",
        request=TherapistQuestionCreateSerializer,
        responses={
            201: inline_serializer(
                name="TherapistQuestionCreateResponse",
                fields={
                    "message": serializers.CharField(),
                    "question": TherapistQuestionSerializer(),
                },
            ),
            403: OpenApiResponse(description="Només els terapeutes poden accedir a aquesta informació."),
            404: OpenApiResponse(description="Pacient no trobat o no assignat."),
        },
    )
    def post(self, request, patient_id):
        patient = self.get_patient(request, patient_id)
        serializer = TherapistQuestionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        TherapistQuestion.objects.filter(patient=patient, is_active=True).update(is_active=False)
        question = serializer.save(
            patient=patient,
            therapist=request.user.therapist_profile,
            is_active=True,
        )
        return Response(
            {
                "message": "Pregunta creada correctament.",
                "question": TherapistQuestionSerializer(question).data,
            },
            status=status.HTTP_201_CREATED,
        )


class TherapistPatientQuestionDetailView(TherapistPatientMixin, APIView):
    @extend_schema(
        tags=["Entries"],
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


class TherapistPatientEntryExportView(TherapistPatientMixin, APIView):
    @extend_schema(
        tags=["Entries"],
        summary="Exportar una entrada d'un pacient a PDF",
        operation_id="entries_export_patient_entry",
        responses={200: OpenApiResponse(description="PDF generat correctament.")},
    )
    def get(self, request, patient_id, entry_id):
        patient = self.get_patient(request, patient_id)
        entry = get_object_or_404(self.get_visible_entries_queryset(patient=patient), pk=entry_id)
        pdf_bytes = render_entries_pdf(title="Exportació d'una entrada del pacient", entries=[entry])
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{build_export_filename(prefix="patient-entry", suffix=str(entry.pk)[:8])}"'
        return response


class TherapistPatientEntriesExportView(TherapistPatientMixin, APIView):
    @extend_schema(
        tags=["Entries"],
        summary="Exportar l'historial visible d'un pacient a PDF",
        operation_id="entries_export_patient_history",
        responses={200: OpenApiResponse(description="PDF generat correctament.")},
    )
    def get(self, request, patient_id):
        patient = self.get_patient(request, patient_id)
        entries = list(self.get_visible_entries_queryset(patient=patient))
        pdf_bytes = render_entries_pdf(title="Historial de journaling del pacient", entries=entries)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{build_export_filename(prefix="patient-history", suffix=str(patient.pk)[:8])}"'
        return response

class TherapistAllQuestionsView(APIView):
    permission_classes = [IsTherapistUser]

    @extend_schema(
        tags=["Entries"],
        summary="Llistar totes les preguntes creades pel terapeuta",
        responses={
            200: TherapistQuestionSerializer(many=True),
        },
    )
    def get(self, request):
        therapist = request.user.therapist_profile
        questions = TherapistQuestion.objects.filter(therapist=therapist).select_related("patient").order_by("-created_at")
        
        return Response(TherapistQuestionSerializer(questions, many=True).data, status=status.HTTP_200_OK)
