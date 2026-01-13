from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Authentication
    path('signup/', signup_view, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='student/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Dashboard & Discovery
    path('dashboard/', track_status, name='track_status'),
    path('program/<int:program_id>/', program_details, name='program_details'),
    path('apply/<int:program_id>/', apply_now, name='apply_now'),
    
    # Learning & Progress
    path('my-learning/', my_learning_view, name='my_learning'),
    path('attendance/<int:application_id>/', view_attendance, name='view_attendance'),
    path('download-certificate/<int:application_id>/', download_certificate, name='download_certificate'),
    
    # Profile
    path('profile/', profile_view, name='profile_view'),
]