from django.urls import path
from . import student_views

app_name = 'student'

urlpatterns = [
    path('dashboard/', student_views.dashboard, name='dashboard'),
    path('search/', student_views.search_programs, name='search'),
    path('programs/', student_views.program_list, name='programs'),
    path('programs/<int:program_id>/', student_views.program_detail, name='program_detail'),
    path('apply/<str:program_type>/<int:program_id>/', student_views.apply_for_program, name='apply'),
    path('applications/', student_views.my_applications, name='applications'),
    path('attendance/', student_views.my_attendance, name='attendance'),
    path('certificates/', student_views.my_certificates, name='certificates'),
    path('certificate/<int:certificate_id>/download/', student_views.download_certificate, name='download_certificate'),
    path('profile/', student_views.profile, name='profile'),
]
