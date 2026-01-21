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
from django.db.models import Q
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.conf import settings
import logging
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except Exception:
    WEASYPRINT_AVAILABLE = False
    logging.getLogger(__name__).warning('WeasyPrint not available; PDF export endpoint will return instructions.')
from courses.models import Course
from internships.models import Internship


@admin_required
def certificate_list(request):
    """List all certificates"""
    certificates = Certificate.objects.select_related(
        'application__student', 'application__course', 'application__internship', 'approved_by'
    ).all()
    templates = CertificateTemplate.objects.all()
    return render(request, 'admin/certificates.html', {
        'certificates': certificates,
        'templates': templates
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
    """Approve a certificate and mark it as ISSUED so student can download"""
    certificate = get_object_or_404(Certificate, id=certificate_id)
    
    if not certificate.is_eligible:
        messages.error(request, 'Cannot approve certificate. Student does not meet eligibility criteria.')
        return redirect('certificate_detail', certificate_id=certificate_id)
    
    certificate.status = 'ISSUED'
    certificate.approved_by = request.user
    certificate.issued_by = request.user
    certificate.issued_date = timezone.now().date()
    if not certificate.certificate_number:
        certificate.generate_certificate_number()
    certificate.save()
    
    messages.success(request, f'Certificate for {certificate.application.student.username} approved and issued successfully. Student can now download it.')
    return redirect('certificate_list')


@admin_required
def issue_certificate(request, certificate_id):
    """Confirm certificate status and redirect"""
    certificate = get_object_or_404(Certificate, id=certificate_id)
    if certificate.status != 'ISSUED':
        # If somehow accessed while not issued, use the approve logic
        certificate.status = 'ISSUED'
        certificate.approved_by = request.user
        certificate.issued_by = request.user
        certificate.issued_date = timezone.now().date()
        if not certificate.certificate_number:
            certificate.generate_certificate_number()
        certificate.save()
        messages.success(request, f'Certificate for {certificate.application.student.username} issued successfully.')
    else:
        messages.info(request, "This certificate is already issued and available for student download.")
    return redirect('certificate_list')


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
        # Show if no certificate exists, OR status is PENDING, OR status is APPROVED (ready for issuance)
        if cert is None or cert.status in ['PENDING', 'APPROVED']:
            eligible_list.append({
                'application': app,
                'certificate': cert
            })
    
    return render(request, 'admin/eligible_students.html', {
        'eligible_list': eligible_list
    })

@admin_required
def html_certificate_preview(request):
    """Render an HTML preview of a certificate (Admin only)."""
    student_name = request.GET.get('student_name', 'Tester Tester')
    course_name = request.GET.get('course_name', 'Mern stack')
    return render(request, 'certificates/html_certificate.html', {
        'student_name': student_name,
        'course_name': course_name,
    })

@admin_required
def certificate_preview_pdf(request):
    """Return a PDF generated from the HTML certificate using WeasyPrint (Admin only).
    If WeasyPrint is not installed, show a short message explaining how to install it.
    """
    student_name = request.GET.get('student_name', 'Tester Tester')
    course_name = request.GET.get('course_name', 'Mern stack')

    html = render_to_string('certificates/html_certificate.html', {
        'student_name': student_name,
        'course_name': course_name,
    })

    if not WEASYPRINT_AVAILABLE:
        return HttpResponse(
            "WeasyPrint is not installed on this server. Install it with: \n\n" \
            "pip install weasyprint\n\nThen make sure libpango/cairo dependencies are available on your system.",
            content_type='text/plain',
            status=500
        )

    # Generate PDF
    pdf_file = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificate_preview_{student_name.replace(" ","_")}.pdf"'
    return response
@login_required
def generate_certificates_view(request):
    """Generate bulk certificates for students"""
    # 1. Fetch data for dropdowns
    user = request.user
    
    # Filter institutions based on role
    # Filter institutions based on role
    if user.role == 'ADMIN' or user.is_superuser:
        institutions = Institution.objects.all()
    else:
        messages.error(request, "Access denied. Only Admins can generate certificates.")
        return redirect('admin_dashboard')

    templates = CertificateTemplate.objects.all()
    
    students = None
    courses = []
    internships = []
    
    selected_institution_id = request.GET.get('college_id')
    selected_course_id = request.GET.get('course_id')
    
    # Auto-select institution for coordinator
    # 2. FILTER LOGIC
    if selected_institution_id and selected_institution_id.isdigit():
        institution_id = int(selected_institution_id)

        # Base student query (approved students)
        students_query = User.objects.filter(
            institution_id=institution_id,
            role='STUDENT',
            approval_status='APPROVED'
        )
        
        # Get Programs
        courses = Course.objects.filter(institution_id=institution_id, is_active=True)
        internships = Internship.objects.filter(institution_id=institution_id, is_active=True)

        # Apply Filters
        if selected_course_id:
            # Parse program selection "type_id"
            try:
                if '_' in str(selected_course_id):
                    p_type, p_id = selected_course_id.split('_')
                else:
                    # Fallback for old integer IDs (default to course)
                    p_type, p_id = 'course', selected_course_id
                
                if p_type == 'course':
                    students_query = students_query.filter(applications__course_id=p_id).distinct()
                elif p_type == 'internship':
                    students_query = students_query.filter(applications__internship_id=p_id).distinct()
                
                # Attach status info to each student for the template
                students = list(students_query.prefetch_related('applications', 'applications__certificate'))
                for student in students:
                    student.app_status = 'NONE'
                    student.cert_status = 'NONE'
                    student.is_eligible = False
                    for app in student.applications.all():
                        is_match = False
                        if p_type == 'course' and str(app.course_id) == str(p_id):
                            is_match = True
                        elif p_type == 'internship' and str(app.internship_id) == str(p_id):
                            is_match = True
                        
                        if is_match:
                            student.app_status = app.status
                            # Get certificate status
                            cert = getattr(app, 'certificate', None)
                            student.cert_status = cert.status if cert else 'NONE'
                            
                            # Eligibility for generation: 
                            # 1. Application must be APPROVED
                            # 2. Coordinator must have APPROVED the certificate (status is 'APPROVED')
                            # Note: If admin wants to generate anyway, they can, but we show status.
                            student.is_eligible = (app.status == 'APPROVED' and student.cert_status == 'APPROVED')
                            
                            # If certificate is already ISSUED, it's not "eligible" for re-generation in this list (or keep it if you want)
                            if student.cert_status == 'ISSUED':
                                student.is_eligible = False
                            break
            except (ValueError, AttributeError):
                students = students_query
        else:
            students = students_query

    # 3. GENERATION LOGIC (POST)
    if request.method == "POST":
        student_ids = request.POST.getlist('selected_students')
        template_id = request.POST.get('template_id')
        post_course_id = request.POST.get('course_id') # Global dropdown from generator.html
        
        if student_ids and template_id:
            template = CertificateTemplate.objects.get(id=template_id)
            issued_count = 0
            
            for s_id in student_ids:
                student = get_object_or_404(User, id=s_id)
                
                # Determine program ID for this student
                student_course_id = request.POST.get(f'course_id_{s_id}') or post_course_id
                
                if not student_course_id:
                    continue
                    
                try:
                    p_type, p_id = student_course_id.split('_')
                    if p_type == 'course':
                        program = get_object_or_404(Course, id=p_id)
                        filter_kwargs = {'course': program}
                    elif p_type == 'internship':
                        program = get_object_or_404(Internship, id=p_id)
                        filter_kwargs = {'internship': program}
                    else:
                        continue
                except (ValueError, Course.DoesNotExist, Internship.DoesNotExist):
                    continue
                
                # Find the application
                application = Application.objects.filter(
                    student=student, 
                    status='APPROVED',
                    **filter_kwargs
                ).first()
                
                if application:
                    # Create or get certificate
                    cert, created = Certificate.objects.get_or_create(
                        application=application,
                        defaults={
                            'status': 'ISSUED',
                            'issued_by': user,
                            'issued_date': timezone.now().date(),
                            'is_eligible': True
                        }
                    )
                    
                    # Update status and template if it already existed but wasn't issued
                    cert.status = 'ISSUED'
                    cert.template = template
                    cert.issued_by = user
                    cert.issued_date = timezone.now().date()
                    if not cert.certificate_number:
                        cert.generate_certificate_number()
                    cert.save()
                    issued_count += 1
            
            if issued_count > 0:
                messages.success(request, f'Successfully approved and issued {issued_count} certificates. Students can now download them.')
            else:
                messages.warning(request, "No valid applications found for selected students/program.")
            
            # Redirect back to the same page or certificate list
            return redirect('certificate_list')

    return render(request, 'certificates/generator.html', {
        'colleges': institutions,
        'templates': templates,
        'students': students,
        'courses': courses,
        'internships': internships,
        'selected_college_id': int(selected_institution_id) if selected_institution_id and selected_institution_id.isdigit() else None,
        'selected_course_id': str(selected_course_id) if selected_course_id else ""
    })

@admin_required
def regenerate_certificate(request, certificate_id):
    """Reset certificate status so it can be re-issued"""
    certificate = get_object_or_404(Certificate, id=certificate_id)
    certificate.status = 'APPROVED'
    certificate.save()
    messages.info(request, f'Certificate for {certificate.application.student.username} reset to APPROVED.')
    return redirect('certificate_list')

@admin_required
def delete_certificate(request, certificate_id):
    """Delete a certificate record"""
    certificate = get_object_or_404(Certificate, id=certificate_id)
    student_name = certificate.application.student.username
    certificate.delete()
    messages.success(request, f'Certificate for {student_name} deleted successfully.')
    return redirect('certificate_list')