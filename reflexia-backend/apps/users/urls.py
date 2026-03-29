from django.http import JsonResponse
from django.urls import path

from apps.users.views import PatientActivationView, PatientRegistrationView, TherapistRegistrationView

def index(request):
    return JsonResponse({"message": "Reflexia API working!"})


urlpatterns = [
    path('', index),
    path('auth/register/therapist/', TherapistRegistrationView.as_view(), name='therapist-register'),
    path('auth/register/patient/', PatientRegistrationView.as_view(), name='patient-register'),
    path('auth/activate/patient/', PatientActivationView.as_view(), name='patient-activate'),
]
