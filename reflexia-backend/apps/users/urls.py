from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def index(request):
    return JsonResponse({"message": "Reflexia API working!"})


urlpatterns = [
    path('', index),
]