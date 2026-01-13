from django.urls import path
from .views import approve_certificates

urlpatterns = [
    path('approve/', approve_certificates, name='approve_certificates'),
]
