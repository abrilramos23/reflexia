from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analysis.models import EmotionalAnalysis
from apps.analysis.serializers import AnalysisCorrectionSerializer, EmotionalAnalysisSerializer
from apps.analysis.services import AnalysisServiceError, analyze_journal_entry, build_evolution_payload
from apps.entries.models import JournalEntry
from apps.entries.serializers import JournalEntrySerializer
from apps.users.models import Patient
from apps.users.permissions import IsTherapistUser


VISIBLE_ENTRY_STATUSES = [JournalEntry.STATUS_ACTIVE, JournalEntry.STATUS_MODIFIED]


class PatientAnalysisMixin:
    permission_classes = [IsAuthenticated]

    def get_patient(self, request):
        return getattr(request.user, "patient_profile", None)

    def ensure_patient(self, request):
        patient = self.get_patient(request)
        if patient is None:
            return None, Response({"detail": "Només els pacients poden accedir a les anàlisis."}, status=status.HTTP_403_FORBIDDEN)
        return patient, None


class PatientEntryAnalysisView(PatientAnalysisMixin, APIView):
    @extend_schema(
        tags=["Analysis"],
        summary="Consultar l'anàlisi d'una entrada",
        responses={
            200: EmotionalAnalysisSerializer,
            202: OpenApiResponse(description="Anàlisi encara no generada."),
            403: OpenApiResponse(description="Només els pacients poden consultar aquesta anàlisi."),
            404: OpenApiResponse(description="Entrada no trobada."),
        },
    )
    def get(self, request, entry_id):
        patient, error_response = self.ensure_patient(request)
        if error_response is not None:
            return error_response

        entry = get_object_or_404(JournalEntry, pk=entry_id, patient=patient, status__in=VISIBLE_ENTRY_STATUSES)
        analysis = getattr(entry, "analysis", None)
        if analysis is None:
            return Response(
                {"detail": "L'anàlisi encara no s'ha generat.", "analysis": None},
                status=status.HTTP_202_ACCEPTED,
            )

        return Response(EmotionalAnalysisSerializer(analysis).data, status=status.HTTP_200_OK)


class PatientAnalyzeEntryView(PatientAnalysisMixin, APIView):
    @extend_schema(
        tags=["Analysis"],
        summary="Generar anàlisi emocional d'una entrada",
        request=None,
        responses={
            200: JournalEntrySerializer,
            403: OpenApiResponse(description="Només els pacients poden analitzar entrades pròpies."),
            404: OpenApiResponse(description="Entrada no trobada."),
            503: OpenApiResponse(description="Servei d'anàlisi no disponible."),
        },
    )
    def post(self, request, entry_id):
        patient, error_response = self.ensure_patient(request)
        if error_response is not None:
            return error_response

        entry = get_object_or_404(
            JournalEntry.objects.select_related("therapist_question"),
            pk=entry_id,
            patient=patient,
            status__in=VISIBLE_ENTRY_STATUSES,
        )

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


class PatientEvolutionView(PatientAnalysisMixin, APIView):
    @extend_schema(
        tags=["Analysis"],
        summary="Consultar evolució emocional pròpia",
        responses={200: OpenApiResponse(description="Dades cronològiques d'evolució emocional.")},
    )
    def get(self, request):
        patient, error_response = self.ensure_patient(request)
        if error_response is not None:
            return error_response

        return Response(build_evolution_payload(patient=patient), status=status.HTTP_200_OK)


class TherapistPatientAnalysisMixin:
    permission_classes = [IsTherapistUser]

    def get_patient(self, request, patient_id):
        therapist = request.user.therapist_profile
        return get_object_or_404(
            Patient,
            pk=patient_id,
            therapist_links__therapist=therapist,
            therapist_links__is_active=True,
        )


class TherapistPatientEntryAnalysisView(TherapistPatientAnalysisMixin, APIView):
    @extend_schema(
        tags=["Analysis"],
        summary="Consultar o corregir l'anàlisi emocional d'una entrada d'un pacient",
        responses={
            200: EmotionalAnalysisSerializer,
            202: OpenApiResponse(description="Anàlisi encara no generada."),
            403: OpenApiResponse(description="Només terapeutes assignats."),
            404: OpenApiResponse(description="Pacient, entrada o anàlisi no trobats."),
        },
    )
    def get(self, request, patient_id, entry_id):
        patient = self.get_patient(request, patient_id)
        entry = get_object_or_404(JournalEntry, pk=entry_id, patient=patient, status__in=VISIBLE_ENTRY_STATUSES)
        analysis = getattr(entry, "analysis", None)
        if analysis is None:
            return Response(
                {"detail": "L'anàlisi encara no s'ha generat.", "analysis": None},
                status=status.HTTP_202_ACCEPTED,
            )

        return Response(EmotionalAnalysisSerializer(analysis).data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Analysis"],
        summary="Afegir una correcció del terapeuta a l'anàlisi",
        request=AnalysisCorrectionSerializer,
        responses={
            200: EmotionalAnalysisSerializer,
            400: OpenApiResponse(description="Correcció no vàlida."),
            403: OpenApiResponse(description="Només terapeutes assignats."),
            404: OpenApiResponse(description="Pacient, entrada o anàlisi no trobats."),
        },
    )
    def patch(self, request, patient_id, entry_id):
        patient = self.get_patient(request, patient_id)
        entry = get_object_or_404(JournalEntry, pk=entry_id, patient=patient, status__in=VISIBLE_ENTRY_STATUSES)
        analysis = get_object_or_404(EmotionalAnalysis, entry=entry)
        serializer = AnalysisCorrectionSerializer(
            analysis,
            data=request.data,
            partial=True,
            context={"therapist": request.user.therapist_profile},
        )
        serializer.is_valid(raise_exception=True)
        analysis = serializer.save()
        return Response(EmotionalAnalysisSerializer(analysis).data, status=status.HTTP_200_OK)


class TherapistPatientEvolutionView(TherapistPatientAnalysisMixin, APIView):
    @extend_schema(
        tags=["Analysis"],
        summary="Consultar evolució emocional d'un pacient assignat",
        responses={
            200: OpenApiResponse(description="Dades cronològiques d'evolució emocional."),
            403: OpenApiResponse(description="Només terapeutes assignats."),
            404: OpenApiResponse(description="Pacient no trobat o no assignat."),
        },
    )
    def get(self, request, patient_id):
        patient = self.get_patient(request, patient_id)
        return Response(build_evolution_payload(patient=patient), status=status.HTTP_200_OK)
