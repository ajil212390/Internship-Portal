from django.contrib import admin
from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['student', 'program_name', 'program_type', 'status', 'applied_at', 'reviewed_by', 'highest_qualification_other']
    list_filter = ['status', 'course__institution', 'internship__institution']
    search_fields = ['student__username', 'course__name', 'internship__title', 'highest_qualification_other']
    ordering = ['-applied_at']
    list_per_page = 25
    date_hierarchy = 'applied_at'
