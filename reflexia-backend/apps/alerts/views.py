from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Q

from apps.alerts.models import Alert, AlertNotification
from apps.alerts.serializers import (
    AlertListSerializer,
    AlertDetailSerializer,
    AlertValidationSerializer,
    AlertNotifyContactsSerializer,
    AlertNotificationSerializer,
)
from apps.alerts.services import send_alert_email_to_contact
from apps.users.permissions import IsTherapistUser
from apps.contacts.models import DefaultContact


class AlertListView(APIView):
    permission_classes = [IsTherapistUser]

    def get(self, request):
        therapist = request.user.therapist_profile

        alerts = Alert.objects.filter(
            patient__therapist_links__therapist=therapist,
            patient__therapist_links__is_active=True,
        ).select_related("emotional_analysis", "patient", "validating_therapist").distinct()

        status_filter = request.query_params.get("status")
        if status_filter:
            alerts = alerts.filter(status=status_filter)

        risk_level = request.query_params.get("risk_level")
        if risk_level:
            alerts = alerts.filter(risk_level=risk_level)

        patient_id = request.query_params.get("patient_id")
        if patient_id:
            alerts = alerts.filter(patient_id=patient_id)

        order_by = request.query_params.get("order_by", "-created_at")
        alerts = alerts.order_by(order_by)

        serializer = AlertListSerializer(alerts, many=True)
        return Response(serializer.data)


class AlertDetailView(APIView):
    permission_classes = [IsTherapistUser]

    def _get_alert_for_therapist(self, request, alert_id):
        therapist = request.user.therapist_profile
        return get_object_or_404(
            Alert,
            id=alert_id,
            patient__therapist_links__therapist=therapist,
            patient__therapist_links__is_active=True,
        )

    def get(self, request, alert_id):
        alert = self._get_alert_for_therapist(request, alert_id)
        serializer = AlertDetailSerializer(alert)
        return Response(serializer.data)

    def patch(self, request, alert_id):
        alert = self._get_alert_for_therapist(request, alert_id)

        serializer = AlertValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action_type = serializer.validated_data["action"]
        validation_note = serializer.validated_data.get("validation_note", "")

        if action_type == "VALIDATE":
            alert.status = Alert.Status.VALIDATED
        elif action_type == "DISMISS":
            alert.status = Alert.Status.DISMISSED

        alert.validating_therapist = request.user.therapist_profile
        alert.validation_note = validation_note
        alert.validated_at = timezone.now()
        alert.save(
            update_fields=[
                "status",
                "validating_therapist",
                "validation_note",
                "validated_at",
            ]
        )

        return Response(AlertDetailSerializer(alert).data)


class AlertNotifyContactsView(APIView):
    permission_classes = [IsTherapistUser]

    def post(self, request, alert_id):
        therapist = request.user.therapist_profile

        alert = get_object_or_404(
            Alert,
            id=alert_id,
            patient__therapist_links__therapist=therapist,
            patient__therapist_links__is_active=True,
        )

        if alert.status != Alert.Status.VALIDATED:
            raise PermissionDenied(
                "Can only notify contacts for validated alerts."
            )

        serializer = AlertNotifyContactsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contact_ids = serializer.validated_data["contact_ids"]

        contacts = DefaultContact.objects.filter(
            patient=alert.patient,
            contact_id__in=contact_ids,
        ).select_related("contact")

        if not contacts.exists():
            raise ValidationError("No valid contacts found for this patient.")

        from apps.alerts.tasks import batch_send_alerts_to_contacts

        batch_send_alerts_to_contacts.delay(
            str(alert.id),
            [str(c.contact.id) for c in contacts],
        )

        alert.notification_status = Alert.NotificationStatus.NOTIFIED
        alert.last_notified_at = timezone.now()
        alert.save(
            update_fields=["notification_status", "last_notified_at"]
        )

        return Response(
            {
                "notified_count": len(contacts),
                "message": f"Notifications enqueued for {len(contacts)} contact(s)",
            },
            status=status.HTTP_200_OK,
        )


class AlertHistoryView(APIView):
    permission_classes = [IsTherapistUser]

    def get(self, request, alert_id):
        therapist = request.user.therapist_profile
        alert = get_object_or_404(
            Alert,
            id=alert_id,
            patient__therapist_links__therapist=therapist,
            patient__therapist_links__is_active=True,
        )

        notifications = alert.notifications.all()
        serializer = AlertNotificationSerializer(notifications, many=True)
        return Response(serializer.data)


class PatientAlertListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if not user.is_patient:
            raise PermissionDenied("Only patients can view their alerts.")

        patient = user.patient_profile

        alerts = Alert.objects.filter(
            patient=patient,
            status=Alert.Status.VALIDATED,
        ).select_related("emotional_analysis", "validating_therapist").order_by("-created_at")

        serializer = AlertListSerializer(alerts, many=True)
        return Response(serializer.data)
