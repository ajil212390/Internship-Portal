from django.urls import path
from . import views

urlpatterns = [
    path('admin/institutions/', views.institution_list, name='institution_list'),
    path('admin/institutions/add/', views.add_institution, name='add_institution'),
    path('admin/institutions/edit/<int:id>/', views.edit_institution, name='edit_institution'),
    path('admin/institutions/delete/<int:id>/', views.delete_institution, name='delete_institution'),
    path('admin/institutions/toggle/<int:id>/', views.toggle_institution_status, name='toggle_institution_status'),
    path('admin/institutions/<int:id>/', views.institution_detail, name='institution_detail'),
]
