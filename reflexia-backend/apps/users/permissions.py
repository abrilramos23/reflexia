from rest_framework.permissions import BasePermission


class IsTherapistUser(BasePermission):
    message = "Només els terapeutas poden realitzar aquesta acció."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_therapist)


class IsClinicAdminUser(BasePermission):
    message = "Només els administradors de clínica poden realitzar aquesta acció."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_clinic_admin)
