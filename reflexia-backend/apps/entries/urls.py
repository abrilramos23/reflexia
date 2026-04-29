from django.urls import path

from apps.entries.views import (
    JournalEditorContextView,
    JournalEntryDetailView,
    JournalEntryListCreateView,
    TherapistPatientEntriesView,
    TherapistPatientEntryDetailView,
    TherapistPatientQuestionsView,
    TherapistPatientQuestionDetailView,
)

urlpatterns = [
    path("entries/editor/", JournalEditorContextView.as_view(), name="entry-editor-context"),
    path("entries/", JournalEntryListCreateView.as_view(), name="entry-list-create"),
    path("entries/<uuid:entry_id>/", JournalEntryDetailView.as_view(), name="entry-detail"),

    # Therapist-Patient views
    path("auth/patients/<uuid:patient_id>/entries/", TherapistPatientEntriesView.as_view(), name="therapist-patient-entry-list"),
    path("auth/patients/<uuid:patient_id>/entries/<uuid:entry_id>/", TherapistPatientEntryDetailView.as_view(), name="therapist-patient-entry-detail"),
    path("auth/patients/<uuid:patient_id>/questions/", TherapistPatientQuestionsView.as_view(), name="therapist-patient-question-list"),
    path("auth/patients/<uuid:patient_id>/questions/<uuid:question_id>/", TherapistPatientQuestionDetailView.as_view(), name="therapist-patient-question-detail"),
]
