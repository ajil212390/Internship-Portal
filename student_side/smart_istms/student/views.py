from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import InternshipProgram, StudentApplication, Attendance, StudentProfile
from .forms import StudentSignupForm
from django.http import HttpResponse

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
    # Placeholder for PDF generation logic
    application = get_object_or_404(StudentApplication, id=application_id, student=request.user.studentprofile)
    return HttpResponse(f"Generating certificate for {application.program.title}...")

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