from django.http import JsonResponse
from django.urls import path

from apps.users.views import (
    ChangePasswordView,
    ConsentDocumentView,
    DeleteAccountView,
    LoginView,
    LogoutView,
    MeView,
    PasswordForgotView,
    PasswordResetView,
    PatientConsentAcceptView,
    PatientConsentRejectView,
    PatientActivationView,
    PatientRegistrationView,
    TherapistRegistrationView,
    TherapistPatientDeactivateView,
    TwoFactorDisableView,
    TwoFactorEnableView,
    TwoFactorSetupView,
    TwoFactorVerifyView,
)

def index(request):
    return JsonResponse({"message": "Reflexia API working!"})


urlpatterns = [
    path('', index),
    path('auth/consent/document/', ConsentDocumentView.as_view(), name='consent-document'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('auth/delete-account/', DeleteAccountView.as_view(), name='delete-account'),
    path('auth/password/forgot/', PasswordForgotView.as_view(), name='password-forgot'),
    path('auth/password/reset/', PasswordResetView.as_view(), name='password-reset'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('auth/register/therapist/', TherapistRegistrationView.as_view(), name='therapist-register'),
    path('auth/register/patient/', PatientRegistrationView.as_view(), name='patient-register'),
    path('auth/patients/deactivate/', TherapistPatientDeactivateView.as_view(), name='patient-deactivate'),
    path('auth/activate/patient/', PatientActivationView.as_view(), name='patient-activate'),
    path('auth/consent/accept/', PatientConsentAcceptView.as_view(), name='patient-consent-accept'),
    path('auth/consent/reject/', PatientConsentRejectView.as_view(), name='patient-consent-reject'),
    path('auth/2fa/setup/', TwoFactorSetupView.as_view(), name='two-factor-setup'),
    path('auth/2fa/enable/', TwoFactorEnableView.as_view(), name='two-factor-enable'),
    path('auth/2fa/verify/', TwoFactorVerifyView.as_view(), name='two-factor-verify'),
    path('auth/2fa/disable/', TwoFactorDisableView.as_view(), name='two-factor-disable'),
]
