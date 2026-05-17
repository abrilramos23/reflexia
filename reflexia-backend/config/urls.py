from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


def index(request):
    return JsonResponse({"message": "Reflexia API working!"})


urlpatterns = [
    path('', index),
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/users/', include('apps.users.urls')),
    path('api/contacts/', include('apps.contacts.urls')),
    path('api/entries/', include('apps.entries.urls')),
    path('api/analysis/', include('apps.analysis.urls')),
]
