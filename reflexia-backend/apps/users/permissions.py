from rest_framework.permissions import BasePermission


class IsTherapistUser(BasePermission):
    message = "Only therapists can perform this action."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_therapist)


class IsClinicAdminUser(BasePermission):
    message = "Only clinic administrators can perform this action."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_clinic_admin)
