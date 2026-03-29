from django.http import JsonResponse
from django.urls import path

from apps.users.views import TherapistRegistrationView

def index(request):
    return JsonResponse({"message": "Reflexia API working!"})


urlpatterns = [
    path('', index),
    path('auth/register/therapist/', TherapistRegistrationView.as_view(), name='therapist-register'),
]
