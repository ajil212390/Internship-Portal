from django.urls import path
from .views import manage_programs

app_name = 'programs'

urlpatterns = [
    path('', manage_programs, name='manage_programs'),
]
