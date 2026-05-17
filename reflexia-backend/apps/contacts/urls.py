from django.urls import path

from apps.contacts.views import (
    AssociatedContactDetailView,
    AssociatedContactListCreateView,
    AvailableSupportTherapistListView,
    SupportTherapistDeleteView,
    SupportTherapistListCreateView,
)


urlpatterns = [
    path("associated/", AssociatedContactListCreateView.as_view(), name="associated-contact-list-create"),
    path("associated/<uuid:contact_id>/", AssociatedContactDetailView.as_view(), name="associated-contact-detail"),
    path("support-therapists/", SupportTherapistListCreateView.as_view(), name="support-therapist-list-create"),
    path("support-therapists/available/", AvailableSupportTherapistListView.as_view(), name="support-therapist-available"),
    path("support-therapists/<uuid:support_id>/", SupportTherapistDeleteView.as_view(), name="support-therapist-delete"),
]
