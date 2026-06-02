from django.urls import path

from apps.alerts.views import (
    AlertListView,
    AlertDetailView,
    AlertNotifyContactsView,
    AlertHistoryView,
    PatientAlertListView,
)

urlpatterns = [
    path("", AlertListView.as_view(), name="alert-list"),
    path("my-alerts/", PatientAlertListView.as_view(), name="patient-alerts"),
    path("<uuid:alert_id>/", AlertDetailView.as_view(), name="alert-detail"),
    path("<uuid:alert_id>/notify-contacts/", AlertNotifyContactsView.as_view(), name="alert-notify"),
    path("<uuid:alert_id>/history/", AlertHistoryView.as_view(), name="alert-history"),
]
