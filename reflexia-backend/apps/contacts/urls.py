from django.urls import path

from apps.contacts.views import (
    AssociatedContactDetailView,
    AssociatedContactListCreateView,
    AvailableSupportTherapistListView,
    SupportTherapistDeleteView,
    SupportTherapistListCreateView,
)


urlpatterns = [
    path("contacts/associated/", AssociatedContactListCreateView.as_view(), name="associated-contact-list-create"),
    path("contacts/associated/<uuid:contact_id>/", AssociatedContactDetailView.as_view(), name="associated-contact-detail"),
    path("contacts/support-therapists/", SupportTherapistListCreateView.as_view(), name="support-therapist-list-create"),
    path("contacts/support-therapists/available/", AvailableSupportTherapistListView.as_view(), name="support-therapist-available"),
    path("contacts/support-therapists/<uuid:support_id>/", SupportTherapistDeleteView.as_view(), name="support-therapist-delete"),
]
