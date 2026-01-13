from django.urls import path
from .views import (
    attendance_list,
    attendance_by_application,
    mark_attendance,
    attendance_report
)

urlpatterns = [
    path('admin/attendance/', attendance_list, name='attendance_list'),
    path('admin/attendance/application/<int:application_id>/', attendance_by_application, name='attendance_by_application'),
    path('admin/attendance/mark/<int:application_id>/', mark_attendance, name='mark_attendance'),
    path('admin/attendance/report/', attendance_report, name='attendance_report'),
]
