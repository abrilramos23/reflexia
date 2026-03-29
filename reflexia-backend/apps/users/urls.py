from django.http import JsonResponse
from django.urls import path

from apps.users.views import (
    LoginView,
    LogoutView,
    MeView,
    PatientConsentAcceptView,
    PatientConsentRejectView,
    PatientActivationView,
    PatientRegistrationView,
    TherapistRegistrationView,
    TwoFactorDisableView,
    TwoFactorEnableView,
    TwoFactorSetupView,
    TwoFactorVerifyView,
)

def index(request):
    return JsonResponse({"message": "Reflexia API working!"})


urlpatterns = [
    path('', index),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('auth/register/therapist/', TherapistRegistrationView.as_view(), name='therapist-register'),
    path('auth/register/patient/', PatientRegistrationView.as_view(), name='patient-register'),
    path('auth/activate/patient/', PatientActivationView.as_view(), name='patient-activate'),
    path('auth/consent/accept/', PatientConsentAcceptView.as_view(), name='patient-consent-accept'),
    path('auth/consent/reject/', PatientConsentRejectView.as_view(), name='patient-consent-reject'),
    path('auth/2fa/setup/', TwoFactorSetupView.as_view(), name='two-factor-setup'),
    path('auth/2fa/enable/', TwoFactorEnableView.as_view(), name='two-factor-enable'),
    path('auth/2fa/verify/', TwoFactorVerifyView.as_view(), name='two-factor-verify'),
    path('auth/2fa/disable/', TwoFactorDisableView.as_view(), name='two-factor-disable'),
]
