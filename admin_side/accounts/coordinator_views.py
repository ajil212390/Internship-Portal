"""
Coordinator views module for the Smart Internship system.
Handles coordinator-specific functionality: dashboard, course/internship management,
applications, attendance, certificates, and profile.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone

from accounts.decorators import coordinator_required
from accounts.models import User
from courses.models import Course
from internships.models import Internship
from applications.models import Application
from attendance.models import Attendance
from certificates.models import Certificate


@coordinator_required
def dashboard(request):
    """Coordinator dashboard with statistics"""
    coordinator = request.user
    
    # Get courses and internships assigned to this coordinator
    courses = Course.objects.filter(coordinator=coordinator, is_active=True)
    internships = Internship.objects.filter(coordinator=coordinator, is_active=True)
    
    # Get applications for coordinator's programs
    course_ids = courses.values_list('id', flat=True)
    internship_ids = internships.values_list('id', flat=True)
    
    applications = Application.objects.filter(
        Q(course_id__in=course_ids) | Q(internship_id__in=internship_ids)
    )
    
    # Statistics
    total_courses = courses.count()
    total_internships = internships.count()
    total_applications = applications.count()
    pending_applications = applications.filter(status='PENDING').count()
    approved_applications = applications.filter(status='APPROVED').count()
    
    # Recent applications
    recent_applications = applications.order_by('-applied_at')[:5]
    
    # Get total enrolled students
    enrolled_students = applications.filter(status='APPROVED').values('student').distinct().count()
    
    context = {
        'total_courses': total_courses,
        'total_internships': total_internships,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'approved_applications': approved_applications,
        'enrolled_students': enrolled_students,
        'recent_applications': recent_applications,
        'courses': courses[:5],
        'internships': internships[:5],
    }
    return render(request, 'coordinator/dashboard.html', context)


@coordinator_required
def manage_courses(request):
    """List courses assigned to this coordinator"""
    coordinator = request.user
    courses = Course.objects.filter(coordinator=coordinator).order_by('-created_at')
    
    # Get enrollment counts
    for course in courses:
        course.enrolled = Application.objects.filter(course=course, status='APPROVED').count()
        course.pending = Application.objects.filter(course=course, status='PENDING').count()
    
    context = {
        'courses': courses,
    }
    return render(request, 'coordinator/courses.html', context)


@coordinator_required
def manage_internships(request):
    """List internships assigned to this coordinator"""
    coordinator = request.user
    internships = Internship.objects.filter(coordinator=coordinator).order_by('-created_at')
    
    # Get enrollment counts
    for internship in internships:
        internship.enrolled = Application.objects.filter(internship=internship, status='APPROVED').count()
        internship.pending = Application.objects.filter(internship=internship, status='PENDING').count()
    
    context = {
        'internships': internships,
    }
    return render(request, 'coordinator/internships.html', context)


@coordinator_required
def view_applications(request):
    """View applications for coordinator's programs"""
    coordinator = request.user
    status_filter = request.GET.get('status', 'all')
    program_filter = request.GET.get('program', 'all')
    
    # Get coordinator's courses and internships
    courses = Course.objects.filter(coordinator=coordinator)
    internships = Internship.objects.filter(coordinator=coordinator)
    
    course_ids = courses.values_list('id', flat=True)
    internship_ids = internships.values_list('id', flat=True)
    
    applications = Application.objects.filter(
        Q(course_id__in=course_ids) | Q(internship_id__in=internship_ids)
    ).select_related('student', 'course', 'internship').order_by('-applied_at')
    
    # Apply filters
    if status_filter != 'all':
        applications = applications.filter(status=status_filter.upper())
    
    if program_filter == 'course':
        applications = applications.filter(course__isnull=False)
    elif program_filter == 'internship':
        applications = applications.filter(internship__isnull=False)
    
    context = {
        'applications': applications,
        'status_filter': status_filter,
        'program_filter': program_filter,
        'courses': courses,
        'internships': internships,
    }
    return render(request, 'coordinator/applications.html', context)


@coordinator_required
def approve_application(request, application_id):
    """Approve an application"""
    coordinator = request.user
    
    application = get_object_or_404(Application, id=application_id)
    
    # Verify coordinator has access to this application
    if application.course and application.course.coordinator != coordinator:
        messages.error(request, 'You do not have permission to manage this application.')
        return redirect('coordinator:applications')
    if application.internship and application.internship.coordinator != coordinator:
        messages.error(request, 'You do not have permission to manage this application.')
        return redirect('coordinator:applications')
    
    application.status = 'APPROVED'
    application.reviewed_at = timezone.now()
    application.reviewed_by = coordinator
    application.notes = request.POST.get('notes', '')
    application.save()
    
    messages.success(request, f'Application for {application.student.username} approved.')
    return redirect('coordinator:applications')


@coordinator_required
def reject_application(request, application_id):
    """Reject an application"""
    coordinator = request.user
    
    application = get_object_or_404(Application, id=application_id)
    
    # Verify coordinator has access
    if application.course and application.course.coordinator != coordinator:
        messages.error(request, 'You do not have permission to manage this application.')
        return redirect('coordinator:applications')
    if application.internship and application.internship.coordinator != coordinator:
        messages.error(request, 'You do not have permission to manage this application.')
        return redirect('coordinator:applications')
    
    application.status = 'REJECTED'
    application.reviewed_at = timezone.now()
    application.reviewed_by = coordinator
    application.notes = request.POST.get('notes', '')
    application.save()
    
    messages.success(request, f'Application for {application.student.username} rejected.')
    return redirect('coordinator:applications')


@coordinator_required
def attendance_list(request):
    """View attendance records for coordinator's programs"""
    coordinator = request.user
    program_filter = request.GET.get('program', '')
    date_filter = request.GET.get('date', '')
    
    # Get coordinator's programs
    courses = Course.objects.filter(coordinator=coordinator)
    internships = Internship.objects.filter(coordinator=coordinator)
    
    # Get approved applications
    course_ids = courses.values_list('id', flat=True)
    internship_ids = internships.values_list('id', flat=True)
    
    applications = Application.objects.filter(
        Q(course_id__in=course_ids) | Q(internship_id__in=internship_ids),
        status='APPROVED'
    ).select_related('student', 'course', 'internship')
    
    # Get attendance records
    attendance_records = Attendance.objects.filter(
        application__in=applications
    ).select_related('application', 'application__student').order_by('-date')
    
    if date_filter:
        attendance_records = attendance_records.filter(date=date_filter)
    
    context = {
        'attendance_records': attendance_records[:50],
        'applications': applications,
        'courses': courses,
        'internships': internships,
        'date_filter': date_filter,
    }
    return render(request, 'coordinator/attendance.html', context)


@coordinator_required
def mark_attendance(request):
    """Mark attendance for students with MORNING/EVENING sessions"""
    coordinator = request.user
    
    if request.method == 'POST':
        date_str = request.POST.get('date')
        session = request.POST.get('session', 'MORNING')  # MORNING or EVENING
        
        if not date_str:
            messages.error(request, 'Please select a date.')
            return redirect('coordinator:mark_attendance')
        
        if session not in ['MORNING', 'EVENING']:
            messages.error(request, 'Invalid session type.')
            return redirect('coordinator:mark_attendance')
        
        try:
            mark_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Invalid date format.')
            return redirect('coordinator:mark_attendance')
        
        # Get applications to mark
        application_ids = request.POST.getlist('application_ids')
        saved = 0
        
        for app_id in application_ids:
            status = request.POST.get(f'status_{app_id}')
            remarks = request.POST.get(f'remarks_{app_id}', '')
            
            if status:
                try:
                    application = Application.objects.get(id=app_id)
                    Attendance.objects.update_or_create(
                        application=application,
                        date=mark_date,
                        session=session,  # MORNING or EVENING
                        defaults={
                            'status': status,
                            'remarks': remarks,
                            'marked_by': coordinator,
                        }
                    )
                    saved += 1
                except Application.DoesNotExist:
                    pass
        
        messages.success(request, f'Saved {session.lower()} attendance for {saved} students.')
        return redirect('coordinator:attendance')
    
    # GET request - show form
    courses = Course.objects.filter(coordinator=coordinator)
    internships = Internship.objects.filter(coordinator=coordinator)
    
    course_ids = courses.values_list('id', flat=True)
    internship_ids = internships.values_list('id', flat=True)
    
    applications = Application.objects.filter(
        Q(course_id__in=course_ids) | Q(internship_id__in=internship_ids),
        status='APPROVED'
    ).select_related('student', 'course', 'internship')
    
    context = {
        'applications': applications,
        'today': timezone.now().date(),
        'status_choices': Attendance.STATUS_CHOICES,
        'session_choices': Attendance.SESSION_CHOICES,
    }
    return render(request, 'coordinator/mark_attendance.html', context)


@coordinator_required
def certificate_list(request):
    """View certificates for coordinator's students"""
    coordinator = request.user
    status_filter = request.GET.get('status', 'all')
    
    # Get coordinator's programs
    courses = Course.objects.filter(coordinator=coordinator)
    internships = Internship.objects.filter(coordinator=coordinator)
    
    course_ids = courses.values_list('id', flat=True)
    internship_ids = internships.values_list('id', flat=True)
    
    # Get approved applications
    applications = Application.objects.filter(
        Q(course_id__in=course_ids) | Q(internship_id__in=internship_ids),
        status='APPROVED'
    )
    
    # Get certificates
    certificates = Certificate.objects.filter(
        application__in=applications
    ).select_related('application', 'application__student', 'application__course', 'application__internship')
    
    if status_filter != 'all':
        certificates = certificates.filter(status=status_filter.upper())
    
    # Also get applications without certificates (eligible for creation)
    apps_without_cert = applications.exclude(certificate__isnull=False)
    
    context = {
        'certificates': certificates,
        'apps_without_cert': apps_without_cert,
        'status_filter': status_filter,
    }
    return render(request, 'coordinator/certificates.html', context)


@coordinator_required
def approve_certificate(request, certificate_id):
    """Approve a certificate"""
    coordinator = request.user
    
    certificate = get_object_or_404(Certificate, id=certificate_id)
    application = certificate.application
    
    # Verify coordinator has access
    if application.course and application.course.coordinator != coordinator:
        messages.error(request, 'You do not have permission to approve this certificate.')
        return redirect('coordinator:certificates')
    if application.internship and application.internship.coordinator != coordinator:
        messages.error(request, 'You do not have permission to approve this certificate.')
        return redirect('coordinator:certificates')
    
    action = request.POST.get('action', 'approve')
    
    if action == 'approve':
        certificate.status = 'APPROVED'
        certificate.approved_by = coordinator
        messages.success(request, f'Certificate approved for {application.student.username}.')
    elif action == 'issue':
        certificate.status = 'ISSUED'
        certificate.issued_date = timezone.now().date()
        certificate.approved_by = coordinator
        messages.success(request, f'Certificate issued for {application.student.username}.')
    elif action == 'reject':
        certificate.status = 'PENDING'
        certificate.remarks = request.POST.get('remarks', '')
        messages.warning(request, f'Certificate rejected for {application.student.username}.')
    
    certificate.save()
    return redirect('coordinator:certificates')


@coordinator_required
def profile(request):
    """View and edit coordinator profile"""
    coordinator = request.user
    
    if request.method == 'POST':
        # Update profile
        coordinator.first_name = request.POST.get('first_name', coordinator.first_name)
        coordinator.last_name = request.POST.get('last_name', coordinator.last_name)
        coordinator.email = request.POST.get('email', coordinator.email)
        coordinator.phone = request.POST.get('phone', coordinator.phone) or None
        coordinator.address = request.POST.get('address', coordinator.address) or None
        
        # Handle profile picture
        if 'profile_picture' in request.FILES:
            coordinator.profile_picture = request.FILES['profile_picture']
        
        coordinator.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('coordinator:profile')
    
    # Get stats
    courses_count = Course.objects.filter(coordinator=coordinator).count()
    internships_count = Internship.objects.filter(coordinator=coordinator).count()
    
    courses = Course.objects.filter(coordinator=coordinator)
    internships = Internship.objects.filter(coordinator=coordinator)
    course_ids = courses.values_list('id', flat=True)
    internship_ids = internships.values_list('id', flat=True)
    
    students_count = Application.objects.filter(
        Q(course_id__in=course_ids) | Q(internship_id__in=internship_ids),
        status='APPROVED'
    ).values('student').distinct().count()
    
    context = {
        'coordinator': coordinator,
        'courses_count': courses_count,
        'internships_count': internships_count,
        'students_count': students_count,
    }
    return render(request, 'coordinator/profile.html', context)


@coordinator_required
def student_list(request):
    """List all students from coordinator's institution"""
    coordinator = request.user
    status_filter = request.GET.get('status', 'all')
    
    # Get students from coordinator's institution
    students = User.objects.filter(
        role='STUDENT',
        institution=coordinator.institution
    ).order_by('-created_at')
    
    # Apply status filter
    if status_filter == 'pending':
        students = students.filter(approval_status='PENDING')
    elif status_filter == 'approved':
        students = students.filter(approval_status='APPROVED')
    elif status_filter == 'rejected':
        students = students.filter(approval_status='REJECTED')
    
    # Get counts
    total_students = User.objects.filter(role='STUDENT', institution=coordinator.institution).count()
    pending_count = User.objects.filter(role='STUDENT', institution=coordinator.institution, approval_status='PENDING').count()
    approved_count = User.objects.filter(role='STUDENT', institution=coordinator.institution, approval_status='APPROVED').count()
    rejected_count = User.objects.filter(role='STUDENT', institution=coordinator.institution, approval_status='REJECTED').count()
    
    context = {
        'students': students,
        'status_filter': status_filter,
        'total_students': total_students,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    }
    return render(request, 'coordinator/students.html', context)


@coordinator_required
def pending_students(request):
    """View students pending approval from coordinator's institution"""
    coordinator = request.user
    
    students = User.objects.filter(
        role='STUDENT',
        institution=coordinator.institution,
        approval_status='PENDING'
    ).order_by('-created_at')
    
    context = {
        'students': students,
        'pending_count': students.count(),
    }
    return render(request, 'coordinator/pending_students.html', context)


@coordinator_required
def approve_student(request, student_id):
    """Approve a student registration"""
    coordinator = request.user
    
    student = get_object_or_404(User, id=student_id, role='STUDENT')
    
    # Verify student is from coordinator's institution
    if student.institution != coordinator.institution:
        messages.error(request, 'You can only approve students from your institution.')
        return redirect('coordinator:students')
    
    if student.approval_status != 'PENDING':
        messages.warning(request, 'This student has already been processed.')
        return redirect('coordinator:students')
    
    student.approval_status = 'APPROVED'
    student.approved_by = coordinator
    student.approval_date = timezone.now()
    student.save()
    
    messages.success(request, f'Student {student.username} has been approved successfully!')
    return redirect('coordinator:students')


@coordinator_required
def reject_student(request, student_id):
    """Reject a student registration"""
    coordinator = request.user
    
    student = get_object_or_404(User, id=student_id, role='STUDENT')
    
    # Verify student is from coordinator's institution
    if student.institution != coordinator.institution:
        messages.error(request, 'You can only reject students from your institution.')
        return redirect('coordinator:students')
    
    if student.approval_status != 'PENDING':
        messages.warning(request, 'This student has already been processed.')
        return redirect('coordinator:students')
    
    rejection_reason = request.POST.get('rejection_reason', 'No reason provided')
    
    student.approval_status = 'REJECTED'
    student.approved_by = coordinator
    student.approval_date = timezone.now()
    student.rejection_reason = rejection_reason
    student.save()
    
    messages.success(request, f'Student {student.username} has been rejected.')
    return redirect('coordinator:students')


@coordinator_required
def student_detail(request, student_id):
    """View detailed information about a student"""
    coordinator = request.user
    
    student = get_object_or_404(User, id=student_id, role='STUDENT')
    
    # Verify student is from coordinator's institution
    if student.institution != coordinator.institution:
        messages.error(request, 'You can only view students from your institution.')
        return redirect('coordinator:students')
    
    # Get student's applications
    applications = Application.objects.filter(student=student).select_related('course', 'internship')
    
    # Get attendance records
    attendance = Attendance.objects.filter(application__student=student).order_by('-date')[:10]
    
    # Get certificates
    certificates = Certificate.objects.filter(application__student=student)
    
    context = {
        'student': student,
        'applications': applications,
        'attendance': attendance,
        'certificates': certificates,
    }
    return render(request, 'coordinator/student_detail.html', context)


@coordinator_required
def attendance_report(request):
    """View attendance report with percentage for all enrolled students"""
    coordinator = request.user
    
    # Get coordinator's programs
    courses = Course.objects.filter(coordinator=coordinator)
    internships = Internship.objects.filter(coordinator=coordinator)
    
    course_ids = courses.values_list('id', flat=True)
    internship_ids = internships.values_list('id', flat=True)
    
    # Get approved applications
    applications = Application.objects.filter(
        Q(course_id__in=course_ids) | Q(internship_id__in=internship_ids),
        status='APPROVED'
    ).select_related('student', 'course', 'internship')
    
    # Calculate attendance for each application
    report_data = []
    for app in applications:
        attendance_percentage = Attendance.get_attendance_percentage(app)
        total_records = Attendance.objects.filter(application=app).count()
        present_count = Attendance.objects.filter(application=app, status__in=['PRESENT', 'LATE']).count()
        absent_count = Attendance.objects.filter(application=app, status='ABSENT').count()
        
        report_data.append({
            'application': app,
            'student': app.student,
            'program_name': app.program_name,
            'total_sessions': total_records,
            'present': present_count,
            'absent': absent_count,
            'percentage': attendance_percentage,
            'eligible': attendance_percentage >= 75,
        })
    
    # Sort by percentage
    report_data.sort(key=lambda x: x['percentage'], reverse=True)
    
    context = {
        'report_data': report_data,
        'courses': courses,
        'internships': internships,
    }
    return render(request, 'coordinator/attendance_report.html', context)


@coordinator_required
def eligible_students(request):
    """View students eligible for certificate (≥75% attendance)"""
    coordinator = request.user
    
    # Get coordinator's programs
    courses = Course.objects.filter(coordinator=coordinator)
    internships = Internship.objects.filter(coordinator=coordinator)
    
    course_ids = courses.values_list('id', flat=True)
    internship_ids = internships.values_list('id', flat=True)
    
    # Get approved applications
    applications = Application.objects.filter(
        Q(course_id__in=course_ids) | Q(internship_id__in=internship_ids),
        status='APPROVED'
    ).select_related('student', 'course', 'internship')
    
    # Filter eligible students (≥75% attendance)
    eligible_list = []
    for app in applications:
        attendance_percentage = Attendance.get_attendance_percentage(app)
        if attendance_percentage >= 75:
            # Check if certificate exists
            has_certificate = hasattr(app, 'certificate')
            certificate_status = app.certificate.status if has_certificate else None
            
            eligible_list.append({
                'application': app,
                'student': app.student,
                'program_name': app.program_name,
                'percentage': attendance_percentage,
                'has_certificate': has_certificate,
                'certificate_status': certificate_status,
            })
    
    context = {
        'eligible_list': eligible_list,
        'total_eligible': len(eligible_list),
    }
    return render(request, 'coordinator/eligible_students.html', context)
