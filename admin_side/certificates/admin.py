from django.contrib import admin
from django.utils import timezone
from .models import Certificate, CertificateTemplate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['application', 'status', 'is_eligible', 'attendance_percentage', 'issued_by', 'issued_date', 'certificate_number']
    list_filter = ['status', 'is_eligible', 'issued_date']
    search_fields = ['application__student__username', 'application__student__email', 'certificate_number']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = ['is_eligible', 'attendance_percentage', 'certificate_number', 'created_at', 'updated_at']
    actions = ['calculate_eligibility', 'issue_certificates']
    
    def calculate_eligibility(self, request, queryset):
        for cert in queryset:
            cert.calculate_eligibility()
            cert.save()
        self.message_user(request, f"Eligibility calculated for {queryset.count()} certificates.")
    calculate_eligibility.short_description = "Calculate eligibility for selected certificates"
    
    def issue_certificates(self, request, queryset):
        issued = 0
        default_template = CertificateTemplate.objects.first()
        for cert in queryset.filter(is_eligible=True, status__in=['PENDING', 'APPROVED']):
            if not cert.template and default_template:
                cert.template = default_template
            if cert.issue(request.user):
                issued += 1
        self.message_user(request, f"Issued {issued} certificates.")
    issue_certificates.short_description = "Issue selected certificates (if eligible)"


@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'font_size', 'name_x_axis', 'name_y_axis', 'created_at']
    search_fields = ['name']
    ordering = ['-created_at']
