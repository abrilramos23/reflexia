from django.urls import path

from apps.entries.views import (
    JournalEditorContextView,
    JournalEntryAnalyzeView,
    JournalEntryDetailView,
    JournalEntryListCreateView,
)


urlpatterns = [
    path("entries/editor/", JournalEditorContextView.as_view(), name="entry-editor-context"),
    path("entries/", JournalEntryListCreateView.as_view(), name="entry-list-create"),
    path("entries/<uuid:entry_id>/", JournalEntryDetailView.as_view(), name="entry-detail"),
    path("entries/<uuid:entry_id>/analyze/", JournalEntryAnalyzeView.as_view(), name="entry-analyze"),
]
