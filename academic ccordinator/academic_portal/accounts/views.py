from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from programs.models import Program
from applications.models import Application
from certificates.models import Certificate
from attendance.models import Attendance

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "accounts/login.html")


@login_required
def dashboard(request):
    # Gather simple counts for dashboard quick-summary cards
    program_count = Program.objects.count()
    total_applications = Application.objects.count()
    approved_applications = Application.objects.filter(status='approved').count()
    certificates_count = Certificate.objects.count()
    attendance_count = Attendance.objects.count()

    context = {
        'program_count': program_count,
        'total_applications': total_applications,
        'approved_applications': approved_applications,
        'certificates_count': certificates_count,
        'attendance_count': attendance_count,
    }

    return render(request, "accounts/dashboard.html", context)


def logout_view(request):
    """Log out the current user and redirect to login page."""
    logout(request)
    return redirect('login')



