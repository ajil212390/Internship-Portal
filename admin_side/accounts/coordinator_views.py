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
    course_ids = list(courses.values_list('id', flat=True))
    internship_ids = list(internships.values_list('id', flat=True))
    
    applications = Application.objects.filter(
        Q(course_id__in=course_ids) | Q(internship_id__in=internship_ids),
        status='APPROVED'
    )
    
    selected_program = request.GET.get('program', '')
    
    attendance_records = Attendance.objects.filter(
        application__in=applications
    ).select_related('application', 'application__student', 'application__course', 'application__internship').order_by('-date', '-session')
    
    session_filter = request.GET.get('session', '')
    query = request.GET.get('q', '')

    if query:
        attendance_records = attendance_records.filter(
            Q(application__student__username__icontains=query) |
            Q(application__student__first_name__icontains=query) |
            Q(application__student__last_name__icontains=query)
        )

    if date_filter:
        attendance_records = attendance_records.filter(date=date_filter)
        
    if session_filter:
        attendance_records = attendance_records.filter(session=session_filter)
        
    if selected_program:
        if selected_program.startswith('course_'):
            c_id = selected_program.split('_')[1]
            attendance_records = attendance_records.filter(application__course_id=c_id)
        elif selected_program.startswith('internship_'):
            i_id = selected_program.split('_')[1]
            attendance_records = attendance_records.filter(application__internship_id=i_id)
    
    # Processed programs for template selection
    processed_courses = []
    for c in courses:
        processed_courses.append({'id': c.id, 'name': c.name, 'val': f"course_{c.id}"})
    
    processed_internships = []
    for i in internships:
        processed_internships.append({'id': i.id, 'name': i.title, 'val': f"internship_{i.id}"})

    context = {
        'attendance_records': attendance_records[:50],
        'applications': applications,
        'courses': processed_courses,
        'internships': processed_internships,
        'date_filter': date_filter,
        'session_filter': session_filter,
        'selected_program': selected_program,
        'query': query,
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
            today = timezone.now().date()
            if mark_date < today:
                messages.error(request, 'Attendance marking for past dates is locked.')
                return redirect('coordinator:mark_attendance')
        except ValueError:
            messages.error(request, 'Invalid date format.')
            return redirect('coordinator:mark_attendance')
        
        # Get applications to mark
        application_ids = request.POST.getlist('application_ids')
        
        if not application_ids:
            messages.warning(request, 'Please select at least one student to mark attendance.')
            return redirect('coordinator:mark_attendance')
        
        saved = 0
        errors = 0
        
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
                    errors += 1
                except Exception as e:
                    errors += 1
                    print(f"Error marking attendance for app {app_id}: {str(e)}")
        
        if saved > 0:
            messages.success(request, f'Successfully saved {session.lower()} attendance for {saved} student(s).')
        if errors > 0:
            messages.warning(request, f'{errors} student(s) had errors.')
        
        return redirect('coordinator:attendance')
    
    # GET request - show form
    selected_program = request.GET.get('program', '')
    courses = Course.objects.filter(coordinator=coordinator)
    internships = Internship.objects.filter(coordinator=coordinator)
    
    # Processed programs for template selection
    processed_courses = []
    for c in courses:
        processed_courses.append({'id': c.id, 'name': c.name, 'val': f"course_{c.id}"})
    
    processed_internships = []
    for i in internships:
        processed_internships.append({'id': i.id, 'name': i.title, 'val': f"internship_{i.id}"})

    # Auto-select program if only one exists
    if not selected_program:
        total_programs = len(processed_courses) + len(processed_internships)
        if total_programs == 1:
            if processed_courses:
                selected_program = processed_courses[0]['val']
            else:
                selected_program = processed_internships[0]['val']

    # Filter applications based on selected program
    applications = Application.objects.filter(status='APPROVED').select_related('student', 'course', 'internship')
    
    if selected_program:
        if selected_program.startswith('course_'):
            c_id = selected_program.split('_')[1]
            applications = applications.filter(course_id=c_id)
        elif selected_program.startswith('internship_'):
            i_id = selected_program.split('_')[1]
            applications = applications.filter(internship_id=i_id)
    else:
        # Default: Show only if assigned to this coordinator
        course_ids = courses.values_list('id', flat=True)
        internship_ids = internships.values_list('id', flat=True)
        applications = applications.filter(
            Q(course_id__in=course_ids) | Q(internship_id__in=internship_ids)
        )
    
    query = request.GET.get('q', '')
    if query:
        applications = applications.filter(
            Q(student__username__icontains=query) |
            Q(student__first_name__icontains=query) |
            Q(student__last_name__icontains=query)
        )


    # Diagnostic data: Check if there are pending applications
    course_ids_all = courses.values_list('id', flat=True)
    internship_ids_all = internships.values_list('id', flat=True)
    pending_count = Application.objects.filter(
        Q(course_id__in=course_ids_all) | Q(internship_id__in=internship_ids_all),
        status='PENDING'
    ).count()

    context = {
        'applications': applications,
        'courses': processed_courses,
        'internships': processed_internships,
        'selected_program': selected_program,
        'pending_count': pending_count,
        'today': timezone.now().date(),
        'status_choices': Attendance.STATUS_CHOICES,
        'session_choices': Attendance.SESSION_CHOICES,
        'query': query,
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
    
    # Identify applications eligible for a certificate but don't have one yet
    # Or have one that was previously rejected/revoked
    eligible_requests = []
    
    # We only care about applications that don't have an active certificate process or are pending approval
    apps_needing_check = applications.exclude(
        certificate__status__in=['APPROVED', 'ISSUED']
    ).select_related('student', 'course', 'internship')

    for app in apps_needing_check:
        attendance_percentage = Attendance.get_attendance_percentage(app)
        if attendance_percentage >= 75:
            eligible_requests.append({
                'application': app,
                'percentage': attendance_percentage,
                'has_cert': hasattr(app, 'certificate'),
                'cert_status': app.certificate.status if hasattr(app, 'certificate') else 'None'
            })
    
    context = {
        'certificates': certificates,
        'eligible_requests': eligible_requests,
        'status_filter': status_filter,
    }
    return render(request, 'coordinator/certificates.html', context)


@coordinator_required
def approve_certificate(request, certificate_id):
    """Approve a certificate application from Coordinator dashboard"""
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
        messages.success(request, f'Certificate approved and sent to Admin for {application.student.username}.')
    elif action == 'issue':
        # Historically coordinators could issue, but workflow now says Admin issues.
        # We will set to APPROVED to signal Admin anyway.
        certificate.status = 'APPROVED'
        certificate.approved_by = coordinator
        messages.info(request, f'Certificate approved and sent to Admin for final generation.')
    elif action == 'reject':
        certificate.status = 'PENDING'
        certificate.remarks = request.POST.get('remarks', '')
        messages.warning(request, f'Certificate request for {application.student.username} sent back to pending.')
    
    certificate.save()
    return redirect('coordinator:certificates')


@coordinator_required
def request_certificate(request, application_id):
    """Coordinator approves eligibility and sends request to Admin for generation"""
    coordinator = request.user
    application = get_object_or_404(Application, id=application_id)
    
    # Verify coordinator has access
    if application.course and application.course.coordinator != coordinator:
        messages.error(request, 'Access denied.')
        return redirect(request.META.get('HTTP_REFERER', 'coordinator:certificates'))
    if application.internship and application.internship.coordinator != coordinator:
        messages.error(request, 'Access denied.')
        return redirect(request.META.get('HTTP_REFERER', 'coordinator:certificates'))
    
    # Check eligibility (attendance >= 75%)
    attendance_percentage = Attendance.get_attendance_percentage(application)
    if attendance_percentage < 75:
        messages.error(request, 'Student is not eligible for a certificate (attendance < 75%).')
        return redirect(request.META.get('HTTP_REFERER', 'coordinator:certificates'))
    
    # Create or update certificate record
    cert, created = Certificate.objects.get_or_create(
        application=application,
        defaults={
            'status': 'APPROVED', # Approved by Coordinator -> Sent to Admin
            'is_eligible': True,
            'attendance_percentage': attendance_percentage,
            'approved_by': coordinator
        }
    )
    
    if not created:
        cert.status = 'APPROVED'
        cert.is_eligible = True
        cert.attendance_percentage = attendance_percentage
        cert.approved_by = coordinator
        cert.save()
    
    messages.success(request, f'Certificate for {application.student.username} has been approved and sent to Admin for generation.')
    
    # Redirect back to where they came from (Certificates list or Student Detail)
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
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
    query = request.GET.get('q', '')
    
    # Get coordinator's programs
    courses = Course.objects.filter(coordinator=coordinator)
    internships = Internship.objects.filter(coordinator=coordinator)
    
    # Get students who have applied to coordinator's programs
    students = User.objects.filter(
        role='STUDENT',
        applications__course__in=courses
    ) | User.objects.filter(
        role='STUDENT',
        applications__internship__in=internships
    )
    
    # Ensure they are distinct and prefetch related data
    students = students.distinct().prefetch_related('applications', 'applications__certificate').order_by('-created_at')
    
    if query:
        students = students.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
    
    # Get total count
    total_students = students.count()
    
    context = {
        'students': students,
        'total_students': total_students,
        'query': query,
    }
    return render(request, 'coordinator/students.html', context)





@coordinator_required
def student_detail(request, student_id):
    """View detailed information about a student"""
    coordinator = request.user
    
    student = get_object_or_404(User, id=student_id, role='STUDENT')
    
    # Verify student has applied to at least one of coordinator's programs
    has_access = Application.objects.filter(
        Q(student=student),
        Q(course__coordinator=coordinator) | Q(internship__coordinator=coordinator)
    ).exists()
    
    if not has_access:
        messages.error(request, 'You do not have permission to view this student.')
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
@coordinator_required
def add_course(request):
    """Add a new course for the coordinator's institution"""
    coordinator = request.user
    institution = coordinator.institution
    
    if not institution:
        messages.error(request, "You must be assigned to an institution to add courses.")
        return redirect('coordinator:courses')
        
    if request.method == 'POST':
        Course.objects.create(
            name=request.POST['name'],
            description=request.POST.get('description'),
            institution=institution,
            coordinator=coordinator,
            duration_days=request.POST.get('duration_days', 30),
            max_students=request.POST.get('max_students', 50),
            start_date=request.POST.get('start_date') or None,
            end_date=request.POST.get('end_date') or None,
            eligibility=request.POST.get('eligibility'),
            category=request.POST.get('category', 'OTHER'),
        )
        messages.success(request, f"Course '{request.POST['name']}' created successfully.")
        return redirect('coordinator:courses')
    
    return render(request, 'coordinator/add_course.html', {
        'categories': Course.CATEGORY_CHOICES
    })


@coordinator_required
def edit_course(request, course_id):
    """Edit an existing course"""
    coordinator = request.user
    course = get_object_or_404(Course, id=course_id, coordinator=coordinator)
    
    if request.method == 'POST':
        course.name = request.POST['name']
        course.description = request.POST.get('description')
        course.duration_days = request.POST.get('duration_days', 30)
        course.max_students = request.POST.get('max_students', 50)
        course.start_date = request.POST.get('start_date') or None
        course.end_date = request.POST.get('end_date') or None
        course.eligibility = request.POST.get('eligibility')
        course.category = request.POST.get('category', 'OTHER')
        course.save()
        messages.success(request, f"Course '{course.name}' updated successfully.")
        return redirect('coordinator:courses')
    
    return render(request, 'coordinator/edit_course.html', {
        'course': course,
        'categories': Course.CATEGORY_CHOICES
    })


@coordinator_required
def delete_course(request, course_id):
    """Delete a course"""
    coordinator = request.user
    course = get_object_or_404(Course, id=course_id, coordinator=coordinator)
    course.delete()
    messages.success(request, "Course deleted successfully.")
    return redirect('coordinator:courses')


@coordinator_required
def add_internship(request):
    """Add a new internship for the coordinator's institution"""
    coordinator = request.user
    institution = coordinator.institution
    
    if not institution:
        messages.error(request, "You must be assigned to an institution to add internships.")
        return redirect('coordinator:internships')
        
    if request.method == 'POST':
        Internship.objects.create(
            title=request.POST['title'],
            description=request.POST.get('description'),
            institution=institution,
            coordinator=coordinator,
            duration=request.POST.get('duration', 30),
            max_students=request.POST.get('max_students', 20),
            start_date=request.POST.get('start_date') or None,
            end_date=request.POST.get('end_date') or None,
            requirements=request.POST.get('requirements'),
            skills_gained=request.POST.get('skills_gained'),
            category=request.POST.get('category', 'OTHER'),
            eligibility=request.POST.get('eligibility'),
        )
        messages.success(request, f"Internship '{request.POST['title']}' created successfully.")
        return redirect('coordinator:internships')
    
    return render(request, 'coordinator/add_internship.html', {
        'categories': Internship.CATEGORY_CHOICES
    })


@coordinator_required
def edit_internship(request, internship_id):
    """Edit an existing internship"""
    coordinator = request.user
    internship = get_object_or_404(Internship, id=internship_id, coordinator=coordinator)
    
    if request.method == 'POST':
        internship.title = request.POST['title']
        internship.description = request.POST.get('description')
        internship.duration = request.POST.get('duration', 30)
        internship.max_students = request.POST.get('max_students', 20)
        internship.start_date = request.POST.get('start_date') or None
        internship.end_date = request.POST.get('end_date') or None
        internship.requirements = request.POST.get('requirements')
        internship.skills_gained = request.POST.get('skills_gained')
        internship.category = request.POST.get('category', 'OTHER')
        internship.eligibility = request.POST.get('eligibility')
        internship.save()
        messages.success(request, f"Internship '{internship.title}' updated successfully.")
        return redirect('coordinator:internships')
    
    return render(request, 'coordinator/edit_internship.html', {
        'internship': internship,
        'categories': Internship.CATEGORY_CHOICES
    })


@coordinator_required
def delete_internship(request, internship_id):
    """Delete an internship"""
    coordinator = request.user
    internship = get_object_or_404(Internship, id=internship_id, coordinator=coordinator)
    internship.delete()
    messages.success(request, "Internship deleted successfully.")
    return redirect('coordinator:internships')
