from django.urls import path
from . import coordinator_views

app_name = 'coordinator'

urlpatterns = [
    path('dashboard/', coordinator_views.dashboard, name='dashboard'),
    path('courses/', coordinator_views.manage_courses, name='courses'),
    path('internships/', coordinator_views.manage_internships, name='internships'),
    
    # Student Management (Approval workflow)
    path('students/', coordinator_views.student_list, name='students'),
    path('students/pending/', coordinator_views.pending_students, name='pending_students'),
    path('students/<int:student_id>/', coordinator_views.student_detail, name='student_detail'),
    path('students/<int:student_id>/approve/', coordinator_views.approve_student, name='approve_student'),
    path('students/<int:student_id>/reject/', coordinator_views.reject_student, name='reject_student'),
    
    # Application Management
    path('applications/', coordinator_views.view_applications, name='applications'),
    path('applications/<int:application_id>/approve/', coordinator_views.approve_application, name='approve_application'),
    path('applications/<int:application_id>/reject/', coordinator_views.reject_application, name='reject_application'),
    
    # Attendance Management (Morning/Evening)
    path('attendance/', coordinator_views.attendance_list, name='attendance'),
    path('attendance/mark/', coordinator_views.mark_attendance, name='mark_attendance'),
    path('attendance/report/', coordinator_views.attendance_report, name='attendance_report'),
    
    # Certificates
    path('certificates/', coordinator_views.certificate_list, name='certificates'),
    path('certificates/<int:certificate_id>/approve/', coordinator_views.approve_certificate, name='approve_certificate'),
    path('certificates/eligible/', coordinator_views.eligible_students, name='eligible_students'),
    
    # Profile
    path('profile/', coordinator_views.profile, name='profile'),
]

