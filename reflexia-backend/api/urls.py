from django.urls import path
from . import views

urlpatterns = [
    path('test-db/', views.test_db),
]
