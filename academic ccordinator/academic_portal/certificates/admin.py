from django.contrib import admin
from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
	list_display = ('application', 'approved', 'approved_on')
	list_filter = ('approved',)
	search_fields = ('application__student_name',)
