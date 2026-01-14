"""
Student views module for the Smart Internship system.
Handles all student-related functionality: dashboard, programs, applications, attendance, certificates, profile.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone

from accounts.decorators import student_required
from accounts.models import User
from courses.models import Course
from internships.models import Internship
from applications.models import Application
from attendance.models import Attendance
from certificates.models import Certificate


@student_required
def dashboard(request):
    """Student dashboard with program search and recent applications"""
    student = request.user
    
    # Get search parameters
    query = request.GET.get('q', '')
    program_type = request.GET.get('type', 'all')
    
    # Get available programs
    courses = Course.objects.filter(is_active=True)
    internships = Internship.objects.filter(is_active=True)
    
    if query:
        courses = courses.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(institution__name__icontains=query)
        )
        internships = internships.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(institution__name__icontains=query)
        )
    
    # Get recent applications
    recent_applications = Application.objects.filter(student=student).order_by('-applied_at')[:5]
    
    # Stats
    total_applications = Application.objects.filter(student=student).count()
    approved_applications = Application.objects.filter(student=student, status='APPROVED').count()
    pending_applications = Application.objects.filter(student=student, status='PENDING').count()
    
    context = {
        'courses': courses[:6],
        'internships': internships[:6],
        'recent_applications': recent_applications,
        'total_applications': total_applications,
        'approved_applications': approved_applications,
        'pending_applications': pending_applications,
        'query': query,
        'program_type': program_type,
    }
    return render(request, 'student/dashboard.html', context)


@student_required
def search_programs(request):
    """Search for courses and internships"""
    query = request.GET.get('q', '')
    program_type = request.GET.get('type', 'all')
    institution = request.GET.get('institution', '')
    
    courses = Course.objects.filter(is_active=True)
    internships = Internship.objects.filter(is_active=True)
    
    if query:
        courses = courses.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )
        internships = internships.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )
    
    if institution:
        courses = courses.filter(institution__name__icontains=institution)
        internships = internships.filter(institution__name__icontains=institution)
    
    # Combine into unified list
    programs = []
    
    if program_type in ['all', 'course']:
        for course in courses:
            programs.append({
                'id': course.id,
                'type': 'course',
                'name': course.name,
                'description': course.description,
                'institution': course.institution.name,
                'duration': f"{course.duration_days} days",
                'seats_available': course.available_seats,
                'start_date': course.start_date,
            })
    
    if program_type in ['all', 'internship']:
        for internship in internships:
            programs.append({
                'id': internship.id,
                'type': 'internship',
                'name': internship.title,
                'description': internship.description,
                'institution': internship.institution.name,
                'duration': f"{internship.duration} days",
                'seats_available': internship.available_seats,
                'start_date': internship.start_date,
            })
    
    context = {
        'programs': programs,
        'query': query,
        'program_type': program_type,
        'institution': institution,
    }
    return render(request, 'student/programs.html', context)


@student_required
def program_list(request):
    """List all available programs (courses and internships)"""
    program_type = request.GET.get('type', 'all')
    
    courses = Course.objects.filter(is_active=True)
    internships = Internship.objects.filter(is_active=True)
    
    context = {
        'courses': courses if program_type in ['all', 'course'] else [],
        'internships': internships if program_type in ['all', 'internship'] else [],
        'program_type': program_type,
    }
    return render(request, 'student/programs.html', context)


@student_required
def program_detail(request, program_id):
    """View details of a specific program"""
    program_type = request.GET.get('type', 'course')
    
    if program_type == 'course':
        program = get_object_or_404(Course, id=program_id, is_active=True)
        template_type = 'course'
    else:
        program = get_object_or_404(Internship, id=program_id, is_active=True)
        template_type = 'internship'
    
    # Check if student already applied
    student = request.user
    existing_application = None
    if template_type == 'course':
        existing_application = Application.objects.filter(student=student, course=program).first()
    else:
        existing_application = Application.objects.filter(student=student, internship=program).first()
    
    context = {
        'program': program,
        'program_type': template_type,
        'existing_application': existing_application,
    }
    return render(request, 'student/program_detail.html', context)


@student_required
def apply_for_program(request, program_type, program_id):
    """Apply for a course or internship"""
    student = request.user
    
    if program_type == 'course':
        program = get_object_or_404(Course, id=program_id, is_active=True)
        # Check for existing application
        existing = Application.objects.filter(student=student, course=program).exists()
        if existing:
            messages.warning(request, 'You have already applied for this course.')
            return redirect('student:applications')
        
        # Check available seats
        if program.available_seats <= 0:
            messages.error(request, 'No seats available for this course.')
            return redirect('student:programs')
        
        # Create application
        application = Application.objects.create(
            student=student,
            course=program,
            status='PENDING',
            student_remarks=request.POST.get('remarks', '')
        )
        messages.success(request, f'Successfully applied for {program.name}!')
        
    elif program_type == 'internship':
        program = get_object_or_404(Internship, id=program_id, is_active=True)
        # Check for existing application
        existing = Application.objects.filter(student=student, internship=program).exists()
        if existing:
            messages.warning(request, 'You have already applied for this internship.')
            return redirect('student:applications')
        
        # Check available seats
        if program.available_seats <= 0:
            messages.error(request, 'No seats available for this internship.')
            return redirect('student:programs')
        
        # Create application
        application = Application.objects.create(
            student=student,
            internship=program,
            status='PENDING',
            student_remarks=request.POST.get('remarks', '')
        )
        messages.success(request, f'Successfully applied for {program.title}!')
    else:
        messages.error(request, 'Invalid program type.')
        return redirect('student:programs')
    
    return redirect('student:applications')


@student_required
def my_applications(request):
    """View student's applications"""
    student = request.user
    status_filter = request.GET.get('status', 'all')
    
    applications = Application.objects.filter(student=student).order_by('-applied_at')
    
    if status_filter != 'all':
        applications = applications.filter(status=status_filter.upper())
    
    context = {
        'applications': applications,
        'status_filter': status_filter,
    }
    return render(request, 'student/applications.html', context)


@student_required
def my_attendance(request):
    """View student's attendance records with MORNING/EVENING sessions"""
    student = request.user
    
    # Get approved applications (enrolled programs)
    approved_applications = Application.objects.filter(student=student, status='APPROVED')
    
    # Get attendance for each application
    attendance_data = []
    for app in approved_applications:
        records = Attendance.objects.filter(application=app).order_by('-date', '-session')
        
        # Use the model method for percentage
        percentage = Attendance.get_attendance_percentage(app)
        
        # Calculate session-wise counts
        morning_present = records.filter(session='MORNING', status__in=['PRESENT', 'LATE']).count()
        morning_total = records.filter(session='MORNING').count()
        evening_present = records.filter(session='EVENING', status__in=['PRESENT', 'LATE']).count()
        evening_total = records.filter(session='EVENING').count()
        
        total = records.count()
        present = records.filter(status='PRESENT').count()
        late = records.filter(status='LATE').count()
        absent = records.filter(status='ABSENT').count()
        
        # Check certificate eligibility
        eligible_for_certificate = percentage >= 75
        
        attendance_data.append({
            'application': app,
            'records': records[:20],  # Last 20 records (10 days x 2 sessions)
            'total': total,
            'present': present,
            'late': late,
            'absent': absent,
            'morning_present': morning_present,
            'morning_total': morning_total,
            'evening_present': evening_present,
            'evening_total': evening_total,
            'percentage': round(percentage, 1),
            'eligible_for_certificate': eligible_for_certificate,
        })
    
    context = {
        'attendance_data': attendance_data,
    }
    return render(request, 'student/attendance.html', context)


@student_required
def my_certificates(request):
    """View student's certificates - only for approved enrollments with ≥75% attendance"""
    student = request.user
    
    # Get certificates through applications
    certificates = Certificate.objects.filter(
        application__student=student
    ).select_related('application', 'application__course', 'application__internship')
    
    # Enhance certificates with eligibility info
    for cert in certificates:
        cert.can_download = (cert.status == 'ISSUED' or cert.status == 'APPROVED') and cert.is_eligible
    
    # Get approved applications that might be eligible for certificate
    approved_applications = Application.objects.filter(
        student=student, 
        status='APPROVED'
    ).select_related('course', 'internship')
    
    eligible_for_certificate = []
    for app in approved_applications:
        percentage = Attendance.get_attendance_percentage(app)
        has_certificate = hasattr(app, 'certificate')
        
        eligible_for_certificate.append({
            'application': app,
            'program_name': app.program_name,
            'attendance_percentage': percentage,
            'is_eligible': percentage >= 75,
            'has_certificate': has_certificate,
            'certificate_status': app.certificate.status if has_certificate else None,
        })
    
    context = {
        'certificates': certificates,
        'eligible_for_certificate': eligible_for_certificate,
    }
    return render(request, 'student/certificates.html', context)


@student_required
def download_certificate(request, certificate_id):
    """Download a certificate as PDF"""
    student = request.user
    certificate = get_object_or_404(
        Certificate,
        id=certificate_id,
        application__student=student,
        status__in=['ISSUED', 'APPROVED']
    )
    
    # Generate PDF dynamically
    from certificates.utils import generate_single_certificate
    from certificates.models import CertificateTemplate
    
    # Try to get a default template
    template = CertificateTemplate.objects.first()
    if not template:
        # Fallback if no template exists
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="certificate_{certificate.id}.txt"'
        response.write("Certificate template not found. Please contact administration.")
        return response
        
    student_name = student.get_full_name() or student.username
    program_name = certificate.application.program_name
    institution_name = student.institution.name if student.institution else None
    
    pdf_buffer = generate_single_certificate(
        student_name,
        template.background_image.path,
        template.name_x_axis,
        template.name_y_axis,
        template.font_size,
        course_name=program_name,
        institution_name=institution_name
    )
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Certificate_{student_name}_{program_name}.pdf"'
    response.write(pdf_buffer.getvalue())
    return response


@student_required
def profile(request):
    """View and edit student profile"""
    student = request.user
    
    if request.method == 'POST':
        # Update profile
        student.first_name = request.POST.get('first_name', student.first_name)
        student.last_name = request.POST.get('last_name', student.last_name)
        student.email = request.POST.get('email', student.email)
        student.phone = request.POST.get('phone', student.phone) or None
        student.address = request.POST.get('address', student.address) or None
        
        # Handle profile picture
        if 'profile_picture' in request.FILES:
            student.profile_picture = request.FILES['profile_picture']
        
        student.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('student:profile')
    
    # Get stats for profile page
    total_applications = Application.objects.filter(student=student).count()
    approved_count = Application.objects.filter(student=student, status='APPROVED').count()
    certificates_count = Certificate.objects.filter(application__student=student, status='ISSUED').count()
    
    context = {
        'student': student,
        'total_applications': total_applications,
        'approved_count': approved_count,
        'certificates_count': certificates_count,
    }
    return render(request, 'student/profile.html', context)
