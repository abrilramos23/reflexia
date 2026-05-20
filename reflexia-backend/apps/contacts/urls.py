from django.urls import path

from apps.contacts.views import (
    AssociatedContactDetailView,
    AssociatedContactListCreateView,
    AvailableSupportTherapistListView,
    SupportTherapistDeleteView,
    SupportTherapistListCreateView,
    SupportTherapistRequestListView,
    SupportTherapistRequestRespondView,
)


urlpatterns = [
    path("associated/", AssociatedContactListCreateView.as_view(), name="associated-contact-list-create"),
    path("associated/<uuid:contact_id>/", AssociatedContactDetailView.as_view(), name="associated-contact-detail"),
    path("support-therapists/", SupportTherapistListCreateView.as_view(), name="support-therapist-list-create"),
    path("support-therapists/available/", AvailableSupportTherapistListView.as_view(), name="support-therapist-available"),
    path("support-therapists/requests/", SupportTherapistRequestListView.as_view(), name="support-therapist-request-list"),
    path("support-therapists/requests/<uuid:request_id>/respond/", SupportTherapistRequestRespondView.as_view(), name="support-therapist-request-respond"),
    path("support-therapists/<uuid:support_id>/", SupportTherapistDeleteView.as_view(), name="support-therapist-delete"),
]
