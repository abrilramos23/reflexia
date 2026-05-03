from django.urls import path

from apps.analysis.views import (
    PatientAnalyzeEntryView,
    PatientEntryAnalysisView,
    PatientEvolutionView,
    TherapistPatientEntryAnalysisView,
    TherapistPatientEvolutionView,
)

urlpatterns = [
    path("entries/<uuid:entry_id>/analysis/", PatientEntryAnalysisView.as_view(), name="entry-analysis"),
    path("entries/<uuid:entry_id>/analyze/", PatientAnalyzeEntryView.as_view(), name="entry-analyze"),
    path("analysis/evolution/", PatientEvolutionView.as_view(), name="patient-analysis-evolution"),
    path(
        "auth/patients/<uuid:patient_id>/analysis/evolution/",
        TherapistPatientEvolutionView.as_view(),
        name="therapist-patient-analysis-evolution",
    ),
    path(
        "auth/patients/<uuid:patient_id>/entries/<uuid:entry_id>/analysis/",
        TherapistPatientEntryAnalysisView.as_view(),
        name="therapist-patient-entry-analysis",
    ),
]
