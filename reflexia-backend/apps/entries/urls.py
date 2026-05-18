from django.urls import path

from apps.entries.views import (
    JournalEditorContextView,
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
    path("editor/", JournalEditorContextView.as_view(), name="entry-editor-context"),
    path("", JournalEntryListCreateView.as_view(), name="entry-list-create"),
    path("export/", PatientEntriesExportView.as_view(), name="entry-export-history"),
    path("<uuid:entry_id>/", JournalEntryDetailView.as_view(), name="entry-detail"),
    path("<uuid:entry_id>/export/", PatientEntryExportView.as_view(), name="entry-export"),

    # Therapist-Patient views
    path("patients/<uuid:patient_id>/", TherapistPatientEntriesView.as_view(), name="therapist-patient-entry-list"),
    path("patients/<uuid:patient_id>/export/", TherapistPatientEntriesExportView.as_view(), name="therapist-patient-entry-export-history"),
    path("patients/<uuid:patient_id>/<uuid:entry_id>/", TherapistPatientEntryDetailView.as_view(), name="therapist-patient-entry-detail"),
    path("patients/<uuid:patient_id>/<uuid:entry_id>/notes/", TherapistPatientEntryNotesView.as_view(), name="therapist-patient-entry-notes"),
    path("patients/<uuid:patient_id>/<uuid:entry_id>/export/", TherapistPatientEntryExportView.as_view(), name="therapist-patient-entry-export"),
    path("patients/<uuid:patient_id>/questions/", TherapistPatientQuestionsView.as_view(), name="therapist-patient-question-list"),
    path("patients/<uuid:patient_id>/questions/<uuid:question_id>/", TherapistPatientQuestionDetailView.as_view(), name="therapist-patient-question-detail"),
    path("questions/", TherapistAllQuestionsView.as_view(), name="therapist-question-list-all"),
]
