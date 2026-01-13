from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('mark/', views.mark_attendance, name='mark_attendance'),
    path('student/<int:app_id>/', views.student_attendance, name='student_attendance'),
]
