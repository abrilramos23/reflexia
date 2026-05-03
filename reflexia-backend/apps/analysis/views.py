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


class PatientAnalysisMixin:
    permission_classes = [IsAuthenticated]

    def get_patient(self, request):
        return getattr(request.user, "patient_profile", None)

    def ensure_patient(self, request):
        patient = self.get_patient(request)
        if patient is None:
            return None, Response({"detail": "Only patients can access analyses."}, status=status.HTTP_403_FORBIDDEN)
        return patient, None


class PatientEntryAnalysisView(PatientAnalysisMixin, APIView):
    @extend_schema(
        tags=["analysis"],
        summary="Consultar l'analisi d'una entrada",
        responses={
            200: EmotionalAnalysisSerializer,
            202: OpenApiResponse(description="Analisi encara no generada."),
            403: OpenApiResponse(description="Nomes els pacients poden consultar aquesta analisi."),
            404: OpenApiResponse(description="Entrada no trobada."),
        },
    )
    def get(self, request, entry_id):
        patient, error_response = self.ensure_patient(request)
        if error_response is not None:
            return error_response

        entry = get_object_or_404(JournalEntry, pk=entry_id, patient=patient)
        analysis = getattr(entry, "analysis", None)
        if analysis is None:
            return Response(
                {"detail": "L'analisi encara no s'ha generat.", "analysis": None},
                status=status.HTTP_202_ACCEPTED,
            )

        return Response(EmotionalAnalysisSerializer(analysis).data, status=status.HTTP_200_OK)


class PatientAnalyzeEntryView(PatientAnalysisMixin, APIView):
    @extend_schema(
        tags=["analysis"],
        summary="Generar analisi emocional d'una entrada",
        responses={
            200: JournalEntrySerializer,
            403: OpenApiResponse(description="Nomes els pacients poden analitzar entrades propies."),
            404: OpenApiResponse(description="Entrada no trobada."),
            503: OpenApiResponse(description="Servei d'analisi no disponible."),
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
            deleted_at__isnull=True,
        )

        try:
            analyze_journal_entry(entry=entry)
        except AnalysisServiceError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        entry.refresh_from_db()
        return Response(
            {
                "message": "Analisi generada correctament. Recorda que es orientativa i sera revisada pel terapeuta.",
                "entry": JournalEntrySerializer(entry).data,
            },
            status=status.HTTP_200_OK,
        )


class PatientEvolutionView(PatientAnalysisMixin, APIView):
    @extend_schema(
        tags=["analysis"],
        summary="Consultar evolucio emocional propia",
        responses={200: OpenApiResponse(description="Dades cronologiques d'evolucio emocional.")},
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
        )


class TherapistPatientEntryAnalysisView(TherapistPatientAnalysisMixin, APIView):
    @extend_schema(
        tags=["analysis"],
        summary="Consultar o corregir l'analisi emocional d'una entrada d'un pacient",
        responses={
            200: EmotionalAnalysisSerializer,
            202: OpenApiResponse(description="Analisi encara no generada."),
            403: OpenApiResponse(description="Nomes terapeutes assignats."),
            404: OpenApiResponse(description="Pacient, entrada o analisi no trobats."),
        },
    )
    def get(self, request, patient_id, entry_id):
        patient = self.get_patient(request, patient_id)
        entry = get_object_or_404(JournalEntry, pk=entry_id, patient=patient)
        analysis = getattr(entry, "analysis", None)
        if analysis is None:
            return Response(
                {"detail": "L'analisi encara no s'ha generat.", "analysis": None},
                status=status.HTTP_202_ACCEPTED,
            )

        return Response(EmotionalAnalysisSerializer(analysis).data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["analysis"],
        summary="Afegir una correccio del terapeuta a l'analisi",
        request=AnalysisCorrectionSerializer,
        responses={
            200: EmotionalAnalysisSerializer,
            400: OpenApiResponse(description="Correccio no valida."),
            403: OpenApiResponse(description="Nomes terapeutes assignats."),
            404: OpenApiResponse(description="Pacient, entrada o analisi no trobats."),
        },
    )
    def patch(self, request, patient_id, entry_id):
        patient = self.get_patient(request, patient_id)
        entry = get_object_or_404(JournalEntry, pk=entry_id, patient=patient)
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
        tags=["analysis"],
        summary="Consultar evolucio emocional d'un pacient assignat",
        responses={
            200: OpenApiResponse(description="Dades cronologiques d'evolucio emocional."),
            403: OpenApiResponse(description="Nomes terapeutes assignats."),
            404: OpenApiResponse(description="Pacient no trobat o no assignat."),
        },
    )
    def get(self, request, patient_id):
        patient = self.get_patient(request, patient_id)
        return Response(build_evolution_payload(patient=patient), status=status.HTTP_200_OK)
