from django.contrib import admin
from .models import Course


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'institution', 'coordinator', 'duration_days', 'max_students', 'is_active', 'created_at']
    list_filter = ['is_active', 'institution']
    search_fields = ['name', 'description', 'institution__name']
    ordering = ['-created_at']
    list_per_page = 25
