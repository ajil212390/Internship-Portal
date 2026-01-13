from django.contrib import admin
from .models import InternshipProgram, StudentApplication, Attendance, StudentProfile

# 1. Edit Internship Programs
@admin.register(InternshipProgram)
class InternshipProgramAdmin(admin.ModelAdmin):
    # Removed 'duration' to avoid error. 
    # Check your models.py: is it 'duration_months' or 'duration_weeks'?
    list_display = ('title', 'institution_name', 'location') 
    search_fields = ('title', 'institution_name', 'location')
    list_filter = ('location',)

# 2. Edit Student Profiles
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'college', 'course', 'phone')
    search_fields = ('user__username', 'college', 'course')

# 3. Edit Applications
@admin.register(StudentApplication)
class StudentApplicationAdmin(admin.ModelAdmin):
    # Changed 'applied_on' to 'id' or leave it out if you're unsure of the name.
    # Usually, Django uses 'created_at' or 'applied_at'.
    list_display = ('student', 'program', 'status') 
    list_filter = ('status',) 
    list_editable = ('status',) 
    search_fields = ('student__user__username', 'program__title')

# 4. Edit Attendance Records
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('application', 'date', 'is_present')
    list_filter = ('date', 'is_present')
    search_fields = ('application__student__user__username', 'application__program__title')