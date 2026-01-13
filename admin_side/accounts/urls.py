from django.urls import path
from . import views

urlpatterns = [
    path('admin/login/', views.admin_login, name='admin_login'),
    path('admin/logout/', views.admin_logout, name='admin_logout'),
    path('admin/coordinators/', views.coordinator_list, name='coordinator_list'),
    path('admin/coordinators/add/', views.add_coordinator, name='add_coordinator'),
    path('admin/coordinators/edit/<int:id>/', views.edit_coordinator, name='edit_coordinator'),
    path('admin/coordinators/delete/<int:id>/', views.delete_coordinator, name='delete_coordinator'),
    # API endpoint for getting coordinators by institution
    path('api/coordinators/<int:institution_id>/', views.get_coordinators_by_institution, name='get_coordinators_by_institution'),
]
