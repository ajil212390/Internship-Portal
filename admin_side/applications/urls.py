from django.urls import path
from .views import application_list

urlpatterns = [
    path('admin/applications/', application_list, name='application_list'),
]
