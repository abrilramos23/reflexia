from django.urls import path

from apps.entries.views import (
    JournalEditorContextView,
    JournalEntryDetailView,
    JournalEntryListCreateView,
)

urlpatterns = [
    path("entries/editor/", JournalEditorContextView.as_view(), name="entry-editor-context"),
    path("entries/", JournalEntryListCreateView.as_view(), name="entry-list-create"),
    path("entries/<uuid:entry_id>/", JournalEntryDetailView.as_view(), name="entry-detail"),
]
