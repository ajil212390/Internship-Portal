from django.contrib import admin
from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['application', 'date', 'session', 'status', 'marked_by', 'marked_at']
    list_filter = ['status', 'session', 'date', 'marked_by']
    search_fields = ['application__student__username', 'application__course__name', 'application__internship__title']
    date_hierarchy = 'date'
    ordering = ['-date', '-session']
