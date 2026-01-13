from django.contrib import admin
from .models import Institution


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'coordinator', 'is_active', 'total_courses', 'total_internships', 'created_at']
    list_filter = ['is_active', 'location']
    search_fields = ['name', 'location', 'email']
    ordering = ['name']
    list_per_page = 25
