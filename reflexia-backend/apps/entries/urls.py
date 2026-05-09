from django.urls import path

from apps.entries.views import (
    JournalEditorContextView,
    PatientAnalyzeEntryView,
    PatientEntriesExportView,
    PatientEntryExportView,
    JournalEntryDetailView,
    JournalEntryListCreateView,
    TherapistPatientEntriesView,
    TherapistPatientEntriesExportView,
    TherapistPatientEntryDetailView,
    TherapistPatientEntryExportView,
    TherapistPatientEntryNotesView,
    TherapistPatientQuestionsView,
    TherapistPatientQuestionDetailView,
    TherapistAllQuestionsView,
)

urlpatterns = [
    path("entries/editor/", JournalEditorContextView.as_view(), name="entry-editor-context"),
    path("entries/", JournalEntryListCreateView.as_view(), name="entry-list-create"),
    path("entries/export/", PatientEntriesExportView.as_view(), name="entry-export-history"),
    path("entries/<uuid:entry_id>/", JournalEntryDetailView.as_view(), name="entry-detail"),
    path("entries/<uuid:entry_id>/analyze/", PatientAnalyzeEntryView.as_view(), name="entry-analyze"),
    path("entries/<uuid:entry_id>/export/", PatientEntryExportView.as_view(), name="entry-export"),

    # Therapist-Patient views
    path("auth/patients/<uuid:patient_id>/entries/", TherapistPatientEntriesView.as_view(), name="therapist-patient-entry-list"),
    path("auth/patients/<uuid:patient_id>/entries/export/", TherapistPatientEntriesExportView.as_view(), name="therapist-patient-entry-export-history"),
    path("auth/patients/<uuid:patient_id>/entries/<uuid:entry_id>/", TherapistPatientEntryDetailView.as_view(), name="therapist-patient-entry-detail"),
    path("auth/patients/<uuid:patient_id>/entries/<uuid:entry_id>/notes/", TherapistPatientEntryNotesView.as_view(), name="therapist-patient-entry-notes"),
    path("auth/patients/<uuid:patient_id>/entries/<uuid:entry_id>/export/", TherapistPatientEntryExportView.as_view(), name="therapist-patient-entry-export"),
    path("auth/patients/<uuid:patient_id>/questions/", TherapistPatientQuestionsView.as_view(), name="therapist-patient-question-list"),
    path("auth/patients/<uuid:patient_id>/questions/<uuid:question_id>/", TherapistPatientQuestionDetailView.as_view(), name="therapist-patient-question-detail"),
    path("auth/questions/", TherapistAllQuestionsView.as_view(), name="therapist-question-list-all"),
]
