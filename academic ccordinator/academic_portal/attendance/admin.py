from django.contrib import admin
from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
	list_display = ('student', 'program', 'date', 'status')
	list_filter = ('status', 'program', 'date')
	search_fields = ('student__username', 'student__email')
	list_editable = ('status',)
