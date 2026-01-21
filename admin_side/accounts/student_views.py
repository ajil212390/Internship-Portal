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
            Q(institution__name__icontains=query) |
            Q(institution__location__icontains=query)
        )
        internships = internships.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(institution__name__icontains=query) |
            Q(institution__location__icontains=query)
        )
    
    # Get recent applications (only for active programs)
    recent_applications = Application.objects.filter(
        student=student
    ).filter(
        Q(course__is_active=True) | Q(internship__is_active=True)
    ).order_by('-applied_at')[:5]
    
    # Stats (only for active programs)
    total_applications = Application.objects.filter(
        student=student
    ).filter(
        Q(course__is_active=True) | Q(internship__is_active=True)
    ).count()
    
    approved_applications = Application.objects.filter(
        student=student, 
        status='APPROVED'
    ).filter(
        Q(course__is_active=True) | Q(internship__is_active=True)
    ).count()
    
    pending_applications = Application.objects.filter(
        student=student, 
        status='PENDING'
    ).filter(
        Q(course__is_active=True) | Q(internship__is_active=True)
    ).count()
    
    context = {
        'courses': courses[:6],
        'internships': internships[:6],
        'recent_applications': recent_applications,
        'total_applications': total_applications,
        'approved_applications': approved_applications,
        'pending_applications': pending_applications,
        'query': query,
        'program_type': program_type,
        'categories': Course.CATEGORY_CHOICES,
    }
    return render(request, 'student/dashboard.html', context)


@student_required
def search_programs(request):
    """Search for courses and internships"""
    query = request.GET.get('q', '')
    program_type = request.GET.get('type', 'all')
    institution = request.GET.get('institution', '')
    location = request.GET.get('location', '')
    category = request.GET.get('category', '')
    
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

    if location:
        courses = courses.filter(institution__location__icontains=location)
        internships = internships.filter(institution__location__icontains=location)

    if category:
        courses = courses.filter(category=category)
        internships = internships.filter(category=category)
    
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
        'location': location,
        'category': category,
        'categories': Course.CATEGORY_CHOICES,
    }
    return render(request, 'student/programs.html', context)


@student_required
def api_search_programs(request):
    """API endpoint for fast AJAX searching of programs"""
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    location = request.GET.get('location', '')
    institution = request.GET.get('institution', '')
    
    courses = Course.objects.filter(is_active=True).select_related('institution')
    internships = Internship.objects.filter(is_active=True).select_related('institution')
    
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
    
    if category:
        courses = courses.filter(category=category)
        internships = internships.filter(category=category)
        
    if location:
        courses = courses.filter(institution__location__icontains=location)
        internships = internships.filter(institution__location__icontains=location)

    if institution:
        courses = courses.filter(institution__name__icontains=institution)
        internships = internships.filter(institution__name__icontains=institution)
        
    results = []
    for c in courses:
        results.append({
            'id': c.id,
            'type': 'course',
            'name': c.name,
            'institution': c.institution.name,
            'location': c.institution.location,
            'category': c.get_category_display(),
            'duration': f"{c.duration_days} days",
            'seats': c.available_seats,
            'url': f"/student/programs/{c.id}/?type=course"
        })
    for i in internships:
        results.append({
            'id': i.id,
            'type': 'internship',
            'name': i.title,
            'institution': i.institution.name,
            'location': i.institution.location,
            'category': i.get_category_display(),
            'duration': f"{i.duration} days",
            'seats': i.available_seats,
            'url': f"/student/programs/{i.id}/?type=internship"
        })
        
    return JsonResponse({'results': results})


@student_required
def api_apply_program(request):
    """API endpoint for quick application"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
        
    program_id = request.POST.get('id')
    program_type = request.POST.get('type')
    student = request.user
    
    if program_type == 'course':
        program = get_object_or_404(Course, id=program_id, is_active=True)
        existing = Application.objects.filter(student=student, course=program).exists()
        if existing:
            return JsonResponse({'error': 'Already applied'}, status=400)
        
        if program.available_seats <= 0:
            return JsonResponse({'error': 'No seats available'}, status=400)
            
        Application.objects.create(student=student, course=program, status='PENDING')
        return JsonResponse({'success': True, 'msg': f'Applied for {program.name}'})
        
    elif program_type == 'internship':
        program = get_object_or_404(Internship, id=program_id, is_active=True)
        existing = Application.objects.filter(student=student, internship=program).exists()
        if existing:
            return JsonResponse({'error': 'Already applied'}, status=400)
            
        if program.available_seats <= 0:
            return JsonResponse({'error': 'No seats available'}, status=400)
            
        Application.objects.create(student=student, internship=program, status='PENDING')
        return JsonResponse({'success': True, 'msg': f'Applied for {program.title}'})
        
    return JsonResponse({'error': 'Invalid type'}, status=400)


@student_required
def program_list(request):
    """List all available programs (courses and internships)"""
    program_type = request.GET.get('type', 'all')
    
    courses = Course.objects.filter(is_active=True).select_related('institution')
    internships = Internship.objects.filter(is_active=True).select_related('institution')
    
    # Combine into unified list for the template
    programs = []
    
    if program_type in ['all', 'course']:
        for course in courses:
            programs.append({
                'id': course.id,
                'type': 'course',
                'name': course.name,
                'description': course.description,
                'institution': course.institution.name,
                'location': course.institution.location,
                'duration': f"{course.duration_days} days",
                'seats_available': course.available_seats,
                'start_date': course.start_date,
                'category': course.get_category_display(),
            })
    
    if program_type in ['all', 'internship']:
        for internship in internships:
            programs.append({
                'id': internship.id,
                'type': 'internship',
                'name': internship.title,
                'description': internship.description,
                'institution': internship.institution.name,
                'location': internship.institution.location,
                'duration': f"{internship.duration} days",
                'seats_available': internship.available_seats,
                'start_date': internship.start_date,
                'category': internship.get_category_display(),
            })
    
    # Shuffle or sort programs if needed, for now just list them
    
    context = {
        'programs': programs,
        'program_type': program_type,
        'categories': Course.CATEGORY_CHOICES,
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
    
    applications = Application.objects.filter(
        student=student
    ).filter(
        Q(course__is_active=True) | Q(internship__is_active=True) | Q(course__isnull=True, internship__isnull=True)
    ).order_by('-applied_at')
    
    if status_filter != 'all':
        applications = applications.filter(status=status_filter.upper())
    
    context = {
        'applications': applications,
        'status_filter': status_filter,
    }
    return render(request, 'student/applications.html', context)


@student_required
def my_programs(request):
    """View student's enrolled (approved) programs"""
    student = request.user
    
    # Enrolled means application is APPROVED and program is active
    enrolled_programs = Application.objects.filter(
        student=student,
        status='APPROVED'
    ).filter(
        Q(course__is_active=True) | Q(internship__is_active=True)
    ).select_related('course', 'internship', 'course__institution', 'internship__institution')
    
    context = {
        'enrolled_programs': enrolled_programs,
    }
    return render(request, 'student/my_programs.html', context)


@student_required
def my_attendance(request):
    """View student's attendance records with MORNING/EVENING sessions"""
    student = request.user
    
    # Get approved applications (enrolled programs) that are still active
    approved_applications = Application.objects.filter(
        student=student, 
        status='APPROVED'
    ).filter(
        Q(course__is_active=True) | Q(internship__is_active=True)
    )
    
    # Get Filter Params
    filter_date = request.GET.get('date')
    session_filter = request.GET.get('session')

    # Get attendance for each application
    attendance_data = []
    for app in approved_applications:
        all_records = Attendance.objects.filter(application=app).order_by('-date', '-session')
        
        # Calculate stats from ALL records (unfiltered)
        total = all_records.count()
        present = all_records.filter(status='PRESENT').count()
        late = all_records.filter(status='LATE').count()
        absent = all_records.filter(status='ABSENT').count()
        
        # Calculate session-wise counts (unfiltered)
        morning_present = all_records.filter(session='MORNING', status__in=['PRESENT', 'LATE']).count()
        morning_total = all_records.filter(session='MORNING').count()
        evening_present = all_records.filter(session='EVENING', status__in=['PRESENT', 'LATE']).count()
        evening_total = all_records.filter(session='EVENING').count()

        # Apply Filters to the records list ONLY
        filtered_records = all_records
        if filter_date:
            filtered_records = filtered_records.filter(date=filter_date)
        if session_filter and session_filter != 'ALL':
            filtered_records = filtered_records.filter(session=session_filter)
        
        # Use the model method for percentage (uses all records internally usually, but let's be sure)
        percentage = Attendance.get_attendance_percentage(app)
        
        # Check certificate eligibility
        eligible_for_certificate = percentage >= 75
        
        attendance_data.append({
            'application': app,
            'records': filtered_records, # Only the list is filtered
            'total': total,              # Stats remain overall
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
        'filter_date': filter_date,
        'session_filter': session_filter,
    }
    return render(request, 'student/attendance.html', context)


@student_required
def my_certificates(request):
    """View student's certificates - only for approved enrollments with ≥75% attendance"""
    student = request.user
    
    # Get certificates through applications that are still active
    certificates = Certificate.objects.filter(
        application__student=student
    ).filter(
        Q(application__course__is_active=True) | Q(application__internship__is_active=True)
    ).select_related('application', 'application__course', 'application__internship')
    
    # Enhance certificates with eligibility info using model property
    for cert in certificates:
        cert.can_download_status = cert.can_download
    
    # Get approved applications that might be eligible for certificate (and are still active)
    approved_applications = Application.objects.filter(
        student=student, 
        status='APPROVED'
    ).filter(
        Q(course__is_active=True) | Q(internship__is_active=True)
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
        status='ISSUED'
    )
    
    # Generate PDF dynamically
    from certificates.utils import generate_single_certificate
    from certificates.models import CertificateTemplate
    
    # Try to get the assigned template or a default one
    template = certificate.template or CertificateTemplate.objects.first()
    if not template:
        # Fallback if no template exists
        return HttpResponse("Certificate template not found. Please contact administration.", content_type='text/plain')
        
    student_name = student.get_full_name() or student.username
    program_name = certificate.application.program_name
    
    # Get institution and logo from the program (course or internship)
    program = certificate.application.course or certificate.application.internship
    institution = program.institution if program else None
    institution_name = institution.name if institution else None
    logo_path = institution.logo.path if institution and institution.logo else None
    
    pdf_buffer = generate_single_certificate(
        student_name,
        template.background_image.path,
        template.name_x_axis,
        template.name_y_axis,
        template.font_size,
        course_name=program_name,
        institution_name=institution_name,
        logo_path=logo_path,
        certificate_id=certificate.certificate_number
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
