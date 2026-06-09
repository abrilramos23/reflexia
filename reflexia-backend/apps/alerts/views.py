from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
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

    @extend_schema(
        tags=["Alerts"],
        summary="Llistar alertes del terapeuta",
        description="Obté un llistat d'alertes dels pacients associats al terapeuta. Permet filtrar per estat (pending, validated, dismissed), nivell de risc (high, medium, low) i pacient.",
        parameters=[
            OpenApiParameter(name="status", description="Filtrar per estat de l'alerta: pending, validated, dismissed", required=False, type=str),
            OpenApiParameter(name="risk_level", description="Filtrar per nivell de risc: high, medium, low", required=False, type=str),
            OpenApiParameter(name="patient_id", description="Filtrar per ID del pacient", required=False, type=str),
            OpenApiParameter(name="order_by", description="Ordenar resultats (per defecte: -created_at)", required=False, type=str),
        ],
        responses={200: AlertListSerializer(many=True)},
    )
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

    @extend_schema(
        tags=["Alerts"],
        summary="Obtenir detall d'una alerta",
        description="Obté la informació completa d'una alerta, incloent l'anàlisi emocional, dades del pacient i contactes associats.",
        responses={200: AlertDetailSerializer},
    )
    def get(self, request, alert_id):
        alert = self._get_alert_for_therapist(request, alert_id)
        serializer = AlertDetailSerializer(alert)
        return Response(serializer.data)

    @extend_schema(
        tags=["Alerts"],
        summary="Validar o desestimar una alerta",
        description="Valida o desestima una alerta. S'ha de proporcionar l'acció (VALIDATE o DISMISS). Per validar-la cal indicar una justificació clínica, i opcionalment una nota interna de validació.",
        request=AlertValidationSerializer,
        responses={200: AlertDetailSerializer},
    )
    def patch(self, request, alert_id):
        alert = self._get_alert_for_therapist(request, alert_id)

        serializer = AlertValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action_type = serializer.validated_data["action"]
        validation_note = serializer.validated_data.get("validation_note", "")
        justification = serializer.validated_data.get("justification", "")

        if action_type == "VALIDATE":
            alert.status = Alert.Status.VALIDATED
        elif action_type == "DISMISS":
            alert.status = Alert.Status.DISMISSED

        alert.validating_therapist = request.user.therapist_profile
        alert.validation_note = validation_note
        alert.justification = justification
        alert.validated_at = timezone.now()
        alert.save(
            update_fields=[
                "status",
                "validating_therapist",
                "validation_note",
                "justification",
                "validated_at",
            ]
        )

        return Response(AlertDetailSerializer(alert).data)


class AlertNotifyContactsView(APIView):
    permission_classes = [IsTherapistUser]

    @extend_schema(
        tags=["Alerts"],
        summary="Notificar contactes d'una alerta validada",
        description="Envia notificacions als contactes especificats d'una alerta que ha estat validada. La alerta ha d'estar en estat VALIDATED i cal indicar la justificació que rebran els contactes.",
        request=AlertNotifyContactsSerializer,
        responses={200: None},
    )
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
                "Només es pot notificar als contactes per a alertes validades."
            )

        serializer = AlertNotifyContactsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contact_ids = serializer.validated_data["contact_ids"]
        justification = serializer.validated_data["justification"]

        contacts = DefaultContact.objects.filter(
            patient=alert.patient,
            contact_id__in=contact_ids,
        ).select_related("contact")

        if not contacts.exists():
            raise ValidationError("No s'han trobat contactes vàlids per a aquest pacient.")

        from apps.alerts.tasks import batch_send_alerts_to_contacts

        alert.justification = justification
        alert.notification_status = Alert.NotificationStatus.NOTIFIED
        alert.last_notified_at = timezone.now()
        alert.save(
            update_fields=["justification", "notification_status", "last_notified_at"]
        )

        batch_send_alerts_to_contacts.delay(
            str(alert.id),
            [str(c.contact.id) for c in contacts],
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

    @extend_schema(
        tags=["Alerts"],
        summary="Obtenir historial de notificacions d'una alerta",
        description="Recupera l'historial de totes les notificacions enviades per a una alerta específica.",
        responses={200: AlertNotificationSerializer(many=True)},
    )
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

    @extend_schema(
        tags=["Alerts"],
        summary="Llistar alertes validades del pacient",
        description="Obté un llistat d'alertes validades pel terapeuta i que el pacient ha de conèixer. Només els pacients poden accedir a aquest endpoint.",
        responses={200: AlertListSerializer(many=True)},
    )
    def get(self, request):
        user = request.user

        if not user.is_patient:
            raise PermissionDenied("Només els pacients poden veure les seves alertes.")

        patient = user.patient_profile

        alerts = Alert.objects.filter(
            patient=patient,
            status=Alert.Status.VALIDATED,
        ).select_related("emotional_analysis", "validating_therapist").order_by("-created_at")

        serializer = AlertListSerializer(alerts, many=True)
        return Response(serializer.data)
