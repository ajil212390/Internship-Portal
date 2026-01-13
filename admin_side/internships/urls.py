from django.urls import path
from . import views

urlpatterns = [
    path('admin/internships/', views.internship_list, name='internship_list'),
    path('admin/internships/add/', views.add_internship, name='add_internship'),
    path('admin/internships/edit/<int:id>/', views.edit_internship, name='edit_internship'),
    path('admin/internships/delete/<int:id>/', views.delete_internship, name='delete_internship'),
    path('admin/internships/assign/<int:id>/', views.assign_internship_coordinator, name='assign_internship_coordinator'),
]
