from django.contrib import admin

from apps.contacts.models import AssociatedContact, DefaultContact, SupportTherapist


@admin.register(AssociatedContact)
class AssociatedContactAdmin(admin.ModelAdmin):
    list_display = ("name", "relation", "email", "phone")
    search_fields = ("name", "relation", "email", "phone")


@admin.register(DefaultContact)
class DefaultContactAdmin(admin.ModelAdmin):
    list_display = ("patient", "contact", "is_default")
    list_filter = ("is_default",)
    search_fields = ("patient__email", "contact__name", "contact__email", "contact__phone")


@admin.register(SupportTherapist)
class SupportTherapistAdmin(admin.ModelAdmin):
    list_display = ("therapist", "support", "status", "requested_at", "responded_at")
    list_filter = ("status",)
    search_fields = (
        "therapist__email",
        "therapist__license_number",
        "support__email",
        "support__license_number",
    )
