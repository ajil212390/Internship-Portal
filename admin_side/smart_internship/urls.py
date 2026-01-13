from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as account_views

urlpatterns = [
    # Root redirects to login
    path('', lambda r: redirect('/login/')),
    
    # Unified Authentication URLs
    path('login/', account_views.unified_login, name='login'),
    path('logout/', account_views.user_logout, name='logout'),
    path('register/', account_views.student_register, name='register'),
    
    # Admin URLs (backward compatibility)
    path('admin/login/', account_views.unified_login, name='admin_login'),
    path('admin/logout/', account_views.admin_logout, name='admin_logout'),
    
    # Include app URLs
    path('', include('accounts.urls')),
    path('', include('institutions.urls')),
    path('', include('dashboard.urls')),
    path('', include('courses.urls')),
    path('', include('internships.urls')),
    path('', include('applications.urls')),
    path('', include('attendance.urls')),
    path('', include('certificates.urls')),
    path('admin/batches/', include('batches.urls')),  # Batch management
    
    # Student URLs
    path('student/', include('accounts.student_urls')),
    
    # Coordinator URLs
    path('coordinator/', include('accounts.coordinator_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
