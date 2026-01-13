from django.urls import path
from . import views

urlpatterns = [
    path('admin/courses/', views.course_list, name='course_list'),
    path('admin/courses/add/', views.add_course, name='add_course'),
    path('admin/courses/edit/<int:id>/', views.edit_course, name='edit_course'),
    path('admin/courses/delete/<int:id>/', views.delete_course, name='delete_course'),
    path('admin/courses/assign/<int:id>/', views.assign_course_coordinator, name='assign_course_coordinator'),
]
