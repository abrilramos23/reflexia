from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.users.models import (
    Organisation,
    OrganisationMember,
    Subscription,
    Patient,
    ProfessionalDirectoryEntry,
    Therapist,
    TherapistPatient,
    User,
)


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display  = ("name", "type", "is_active", "created_at")
    list_filter   = ("type", "is_active")
    search_fields = ("name",)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("organisation", "plan", "status", "ini_date", "end_date")
    list_filter = ("plan", "status")


@admin.register(OrganisationMember)
class OrganisationMemberAdmin(admin.ModelAdmin):
    list_display = ("user", "organisation", "is_admin", "joined_at")
    list_filter = ("is_admin", "organisation")
    search_fields = ("user__email", "organisation__name")


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model     = User
    ordering  = ("email",)
    list_display = (
        "email",
        "first_name",
        "last_name",
        "role",
        "is_staff",
        "is_active",
        "two_factor_enabled",
    )
    list_filter   = ("role", "is_staff", "is_active", "two_factor_enabled")
    search_fields = ("email", "first_name", "last_name")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Role", {"fields": ("role",)}),
        ("Security", {"fields": ("two_factor_enabled",)}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "registration_date")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "role",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display  = ("email", "first_name", "last_name", "birth_date", "consent_accepted")
    list_filter   = ("consent_accepted",)
    search_fields = ("email", "first_name", "last_name")


@admin.register(Therapist)
class TherapistAdmin(admin.ModelAdmin):
    list_display  = ("email", "first_name", "last_name", "license_number", "specialty")
    search_fields = ("email", "first_name", "last_name", "license_number", "specialty")


@admin.register(TherapistPatient)
class TherapistPatientAdmin(admin.ModelAdmin):
    list_display  = ("therapist", "patient", "is_active", "created_at")
    list_filter   = ("is_active",)
    search_fields = (
        "patient__email",
        "patient__first_name",
        "patient__last_name",
        "therapist__email",
        "therapist__license_number",
    )


@admin.register(ProfessionalDirectoryEntry)
class ProfessionalDirectoryEntryAdmin(admin.ModelAdmin):
    list_display  = ("license_number", "complete_name")
    search_fields = ("license_number", "complete_name")