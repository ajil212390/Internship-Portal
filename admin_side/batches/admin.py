from django.contrib import admin
from .models import Batch


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ['name', 'institution', 'student_count', 'coordinator_names', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active', 'institution', 'start_date']
    search_fields = ['name', 'description', 'institution__name']
    filter_horizontal = ['coordinators']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'institution')
        }),
        ('Coordinators', {
            'fields': ('coordinators',),
            'description': 'Select one or more coordinators for this batch'
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'max_students')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
