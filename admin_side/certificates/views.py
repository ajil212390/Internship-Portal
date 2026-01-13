from io import BytesIO
import zipfile
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from accounts.decorators import admin_required
from .utils import generate_single_certificate
from .models import Certificate, CertificateTemplate
from applications.models import Application
from institutions.models import Institution
from accounts.models import User


@admin_required
def certificate_list(request):
    """List all certificates"""
    certificates = Certificate.objects.select_related(
        'application__student', 'application__course', 'application__internship', 'approved_by'
    ).all()
    return render(request, 'admin/certificates.html', {
        'certificates': certificates
    })


@admin_required
def certificate_detail(request, certificate_id):
    """View certificate details"""
    certificate = get_object_or_404(Certificate, id=certificate_id)
    return render(request, 'admin/certificate_detail.html', {
        'certificate': certificate
    })


@admin_required
def generate_certificate(request, application_id):
    """Generate certificate for an approved application"""
    application = get_object_or_404(Application, id=application_id, status='APPROVED')
    
    # Check if certificate already exists
    certificate, created = Certificate.objects.get_or_create(application=application)
    
    # Calculate eligibility
    certificate.calculate_eligibility()
    certificate.save()
    
    if created:
        messages.success(request, f'Certificate generated for {application.student.username}')
    else:
        messages.info(request, f'Certificate already exists for {application.student.username}')
    
    return redirect('certificate_detail', certificate_id=certificate.id)


@admin_required
def approve_certificate(request, certificate_id):
    """Approve a certificate"""
    certificate = get_object_or_404(Certificate, id=certificate_id)
    
    if not certificate.is_eligible:
        messages.error(request, 'Cannot approve certificate. Student does not meet eligibility criteria.')
        return redirect('certificate_detail', certificate_id=certificate_id)
    
    certificate.status = 'APPROVED'
    certificate.approved_by = request.user
    certificate.save()
    
    messages.success(request, 'Certificate approved successfully')
    return redirect('certificate_detail', certificate_id=certificate_id)


@admin_required
def issue_certificate(request, certificate_id):
    """Issue a certificate (mark as issued)"""
    certificate = get_object_or_404(Certificate, id=certificate_id, status='APPROVED')
    
    certificate.status = 'ISSUED'
    certificate.issued_date = timezone.now().date()
    certificate.save()
    
    messages.success(request, 'Certificate issued successfully')
    return redirect('certificate_detail', certificate_id=certificate_id)


@admin_required
def revoke_certificate(request, certificate_id):
    """Revoke a certificate"""
    certificate = get_object_or_404(Certificate, id=certificate_id)
    
    if request.method == 'POST':
        certificate.status = 'REVOKED'
        certificate.remarks = request.POST.get('remarks', 'Revoked by admin')
        certificate.save()
        messages.success(request, 'Certificate revoked')
        return redirect('certificate_list')
    
    return render(request, 'admin/revoke_certificate.html', {
        'certificate': certificate
    })


@admin_required
def eligible_students(request):
    """List students eligible for certificates"""
    # Get approved applications that don't have certificates or have pending certificates
    approved_applications = Application.objects.filter(status='APPROVED').select_related(
        'student', 'course', 'internship'
    )
    
    eligible_list = []
    for app in approved_applications:
        cert = getattr(app, 'certificate', None)
        if cert is None or cert.status == 'PENDING':
            eligible_list.append({
                'application': app,
                'certificate': cert
            })
    
    return render(request, 'admin/eligible_students.html', {
        'eligible_list': eligible_list
    })
def generate_certificates_view(request):
    """Generate bulk certificates for students"""
    # 1. Fetch data for dropdowns
    institutions = Institution.objects.all()
    templates = CertificateTemplate.objects.all()
    
    students = None
    batches = []
    selected_institution_id = request.GET.get('college_id')
    selected_batch = request.GET.get('batch')

    # 2. FILTER LOGIC: If an institution is selected, fetch its students and batches
    if selected_institution_id:
        students_query = User.objects.filter(
            institution_id=selected_institution_id,
            role='STUDENT'
        )
        
        # Get unique batches for the selected institution
        batches = students_query.exclude(batch__isnull=True).exclude(batch='').values_list('batch', flat=True).distinct().order_by('-batch')
        
        # Further filter by batch if selected
        if selected_batch:
            students = students_query.filter(batch=selected_batch)
        else:
            students = students_query

    # 3. GENERATION LOGIC: If form is submitted (POST)
    if request.method == "POST":
        student_ids = request.POST.getlist('selected_students')  # Get checked boxes
        template_id = request.POST.get('template_id')
        
        if student_ids and template_id:
            # Fetch the template configuration
            template = CertificateTemplate.objects.get(id=template_id)
            selected_students = User.objects.filter(id__in=student_ids)

            # Create ZIP file in memory
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED) as zf:
                for student in selected_students:
                    # Generate PDF using our utility
                    student_name = student.get_full_name() or student.username
                    institution_name = student.institution.name if student.institution else None
                    
                    pdf_data = generate_single_certificate(
                        student_name,
                        template.background_image.path,
                        template.name_x_axis,
                        template.name_y_axis,
                        template.font_size,
                        course_name=None,  # Can be added later if needed
                        institution_name=institution_name
                    )
                    # Add to ZIP
                    filename = f"{student_name.replace(' ', '_')}_Certificate.pdf"
                    zf.writestr(filename, pdf_data.getvalue())

            # Return the ZIP download
            zip_buffer.seek(0)
            response = HttpResponse(zip_buffer, content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="Certificates.zip"'
            messages.success(request, f'Successfully generated {len(student_ids)} certificates!')
            return response

    return render(request, 'certificates/generator.html', {
        'colleges': institutions,  # Keep template variable name for backward compatibility
        'templates': templates,
        'students': students,
        'batches': batches,
        'selected_college_id': int(selected_institution_id) if selected_institution_id else None,
        'selected_batch': selected_batch
    })