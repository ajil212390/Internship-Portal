from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import InternshipProgram, StudentApplication, Attendance, StudentProfile
from .forms import StudentSignupForm
from django.http import HttpResponse
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4

# --- 1. SIGNUP VIEW ---
def signup_view(request):
    if request.method == 'POST':
        form = StudentSignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = StudentSignupForm()
    return render(request, 'student/signup.html', {'form': form})

# --- 2. DASHBOARD (SEARCH & EXPLORE) ---
@login_required
def track_status(request): 
    programs = InternshipProgram.objects.all()
    
    # Get search parameters
    course = request.GET.get('course')
    inst = request.GET.get('institution')
    place = request.GET.get('place')

    # Apply filters for the "Explore" section
    if course: programs = programs.filter(title__icontains=course)
    if inst: programs = programs.filter(institution_name__icontains=inst)
    if place: programs = programs.filter(location__icontains=place)

    # Fetch user's applications for the "Recent Status" table
    applications = StudentApplication.objects.filter(student=request.user.studentprofile).order_by('-id')

    return render(request, 'student/dashboard.html', {
        'programs': programs,
        'applications': applications
    })

# --- 3. PROGRAM DETAILS & APPLICATION ---
@login_required
def program_details(request, program_id):
    program = get_object_or_404(InternshipProgram, id=program_id)
    return render(request, 'student/program_details.html', {'program': program})

@login_required
def apply_now(request, program_id):
    program = get_object_or_404(InternshipProgram, id=program_id)
    student_profile = request.user.studentprofile
    
    # get_or_create prevents duplicate applications
    StudentApplication.objects.get_or_create(student=student_profile, program=program)
    return redirect('track_status')

# --- 4. MY LEARNING (ATTENDANCE & CERTIFICATES) ---
@login_required
def my_learning_view(request):
    student = request.user.studentprofile
    # Only active or finished courses
    enrolled_apps = StudentApplication.objects.filter(
        student=student, 
        status__in=['Approved', 'Completed']
    )
    
    for app in enrolled_apps:
        records = Attendance.objects.filter(application=app)
        total = records.count()
        present = records.filter(is_present=True).count()
        app.attendance_pct = (present / total * 100) if total > 0 else 0

    return render(request, 'student/my_learning.html', {'enrolled_courses': enrolled_apps})

@login_required
def view_attendance(request, application_id):
    application = get_object_or_404(StudentApplication, id=application_id, student=request.user.studentprofile)
    attendance_records = Attendance.objects.filter(application=application).order_by('-date')
    
    total = attendance_records.count()
    present_count = attendance_records.filter(is_present=True).count()
    percentage = (present_count / total * 100) if total > 0 else 0

    return render(request, 'student/attendance.html', {
        'application': application,
        'attendance_records': attendance_records,
        'percentage': percentage,
        'present_count': present_count,
    })

@login_required
def download_certificate(request, application_id):
    """Generate and return a PDF certificate for a completed program.

    Requirements:
    - The application must belong to the requesting student
    - The application status must be 'Completed'
    - The student's attendance for that application must meet threshold (>=75%)
    """
    application = get_object_or_404(StudentApplication, id=application_id, student=request.user.studentprofile)

    # Verify completion status
    if application.status != 'Completed':
        return HttpResponse('Certificate not available: program not completed.', status=400)

    # Calculate attendance percentage
    records = Attendance.objects.filter(application=application)
    total = records.count()
    present = records.filter(is_present=True).count()
    attendance_pct = (present / total * 100) if total > 0 else 0

    # Threshold (consistent with admin side) - use 75%
    if attendance_pct < 75:
        return HttpResponse('Certificate not available: attendance below required threshold.', status=400)

    # Build PDF
    buffer = BytesIO()
    page_width, page_height = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=landscape(A4))

    # Background / framing
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, page_width, page_height, fill=1, stroke=0)

    # Title
    c.setFont('Helvetica-Bold', 36)
    c.setFillColorRGB(0.05, 0.3, 0.2)
    title = 'COURSE COMPLETED'
    tw = c.stringWidth(title, 'Helvetica-Bold', 36)
    c.drawString((page_width - tw) / 2, page_height - 120, title)

    # Subtitle
    c.setFont('Helvetica', 18)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    subtitle = 'Awarded to:'
    sw = c.stringWidth(subtitle, 'Helvetica', 18)
    c.drawString((page_width - sw) / 2, page_height - 160, subtitle)

    # Student Name
    student_name = request.user.get_full_name() or request.user.username
    c.setFont('Helvetica-Bold', 48)
    c.setFillColorRGB(0, 0.05, 0.1)
    name_w = c.stringWidth(student_name, 'Helvetica-Bold', 48)
    c.drawString((page_width - name_w) / 2, page_height - 230, student_name)

    # Course Name
    course_name = application.program.title
    c.setFont('Helvetica', 20)
    c.setFillColorRGB(0.05, 0.35, 0.6)
    course_w = c.stringWidth(course_name, 'Helvetica', 20)
    c.drawString((page_width - course_w) / 2, page_height - 290, course_name)

    # Attendance / Issued info
    c.setFont('Helvetica', 12)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    info_line = f"Attendance: {attendance_pct:.0f}%"
    c.drawString(80, 80, info_line)
    issue_line = f"Issued to: {student_name} | Program: {course_name}"
    c.drawRightString(page_width - 80, 80, issue_line)

    c.showPage()
    c.save()

    buffer.seek(0)
    response = HttpResponse(content_type='application/pdf')
    filename_safe = student_name.replace(' ', '_')[:50]
    course_safe = course_name.replace(' ', '_')[:50]
    response['Content-Disposition'] = f'attachment; filename="Certificate_{filename_safe}_{course_safe}.pdf"'
    response.write(buffer.getvalue())
    return response

# --- 5. PROFILE VIEW ---
@login_required
def profile_view(request):
    student = request.user.studentprofile
    # Simply show all applications and their statuses
    enrolled_courses = StudentApplication.objects.filter(student=student).order_by('-id')
    
    return render(request, 'student/profile.html', {
        'student': student,
        'enrolled_courses': enrolled_courses
    })