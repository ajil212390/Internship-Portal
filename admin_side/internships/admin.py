from django.contrib import admin
from .models import Internship


@admin.register(Internship)
class InternshipAdmin(admin.ModelAdmin):
    list_display = ['title', 'institution', 'coordinator', 'duration', 'max_students', 'is_active', 'created_at']
    list_filter = ['is_active', 'institution']
    search_fields = ['title', 'description', 'institution__name']
    ordering = ['-created_at']
    list_per_page = 25
