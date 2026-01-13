from django.urls import path
from . import views

app_name = 'batches'

urlpatterns = [
    path('', views.batch_list, name='list'),
    path('add/', views.batch_add, name='add'),
    path('<int:batch_id>/', views.batch_detail, name='detail'),
    path('<int:batch_id>/edit/', views.batch_edit, name='edit'),
    path('<int:batch_id>/delete/', views.batch_delete, name='delete'),
    path('<int:batch_id>/students/', views.batch_students, name='students'),
]
