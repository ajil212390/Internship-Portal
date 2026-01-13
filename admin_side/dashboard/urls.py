from django.urls import path
from .views import admin_dashboard, reports_dashboard, student_list, student_detail, admin_profile

urlpatterns = [
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin/profile/', admin_profile, name='admin_profile'),
    path('admin/reports/', reports_dashboard, name='reports_dashboard'),
    path('admin/students/', student_list, name='student_list'),
    path('admin/students/<int:student_id>/', student_detail, name='student_detail'),
]
