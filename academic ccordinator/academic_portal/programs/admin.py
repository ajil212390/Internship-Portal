from django.contrib import admin
from .models import Program


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
	list_display = ('title', 'program_type', 'price', 'duration', 'is_active')
	list_filter = ('program_type', 'is_active')
	search_fields = ('title', 'description')

