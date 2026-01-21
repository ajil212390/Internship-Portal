from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'institution', 'is_active', 'created_at', 'highest_qualification_other']
    list_filter = ['role', 'is_active', 'institution']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'highest_qualification_other']
    ordering = ['-created_at']
    list_per_page = 25
