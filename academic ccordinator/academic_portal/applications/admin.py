from django.contrib import admin
from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
	list_display = ('student_name', 'email', 'program', 'status', 'applied_on')
	list_filter = ('status', 'program')
	search_fields = ('student_name', 'email')

