from django.shortcuts import render
from django.utils import timezone
from accounts.decorators import admin_required
from accounts.models import User
from institutions.models import Institution
from courses.models import Course
from internships.models import Internship
from applications.models import Application
from itertools import chain
from operator import attrgetter


@admin_required
def admin_dashboard(request):
    """Enhanced admin dashboard with comprehensive statistics"""
    
    # Basic counts
    total_institutions = Institution.objects.count()
    total_coordinators = User.objects.filter(role='COORDINATOR').count()
    total_students = User.objects.filter(role='STUDENT').count()
    total_courses = Course.objects.count()
    total_internships = Internship.objects.count()
    
    # Application statistics
    total_applications = Application.objects.count()
    pending_applications = Application.objects.filter(status='PENDING').count()
    approved_applications = Application.objects.filter(status='APPROVED').count()
    rejected_applications = Application.objects.filter(status='REJECTED').count()
    
    # Institution statistics
    active_institutions = Institution.objects.filter(is_active=True).count()
    assigned_institutions = Institution.objects.exclude(coordinator=None).count()
    
    # Active courses and internships
    active_courses = Course.objects.filter(is_active=True).count()
    active_internships = Internship.objects.filter(is_active=True).count()
    
    # Recent data
    recent_applications = Application.objects.select_related(
        'student', 'course', 'internship'
    ).order_by('-applied_at')[:5]
    
    recent_students = User.objects.filter(role='STUDENT').order_by('-created_at')[:5]
    
    # Build recent activities from actual data
    recent_activities = []
    
    # Recent institutions
    for inst in Institution.objects.order_by('-created_at')[:5]:
        recent_activities.append({
            'date': inst.created_at,
            'name': inst.name,
            'type': 'Institution',
            'status': 'Active' if inst.is_active else 'Inactive',
            'icon': 'building',
            'url': f'/admin/institutions/{inst.id}/'
        })
    
    # Recent coordinators
    for coord in User.objects.filter(role='COORDINATOR').order_by('-created_at')[:5]:
        recent_activities.append({
            'date': coord.created_at,
            'name': coord.username,
            'type': 'Coordinator',
            'status': 'Active' if coord.is_active else 'Inactive',
            'icon': 'user-tie',
            'url': f'/admin/coordinators/edit/{coord.id}/'
        })
    
    # Sort by date descending and take top 5
    recent_activities = sorted(recent_activities, key=lambda x: x['date'], reverse=True)[:5]
    
    context = {
        # Basic counts
        'total_institutions': total_institutions,
        'total_coordinators': total_coordinators,
        'total_students': total_students,
        'total_courses': total_courses,
        'total_internships': total_internships,
        
        # Application stats
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'approved_applications': approved_applications,
        'rejected_applications': rejected_applications,
        
        # Institution stats
        'active_institutions': active_institutions,
        'assigned_institutions': assigned_institutions,
        
        # Active counts
        'active_courses': active_courses,
        'active_internships': active_internships,
        
        # Recent data
        'recent_applications': recent_applications,
        'recent_students': recent_students,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'admin/dashboard.html', context)


@admin_required
def reports_dashboard(request):
    """Enhanced reports and analytics view with time-series data"""
    from django.db.models import Count, Q
    from django.db.models.functions import TruncMonth
    from datetime import datetime, timedelta
    
    # 1. Applications by status
    applications_by_status = Application.objects.values('status').annotate(
        count=Count('id')
    )
    
    # 2. Monthly registration trends (Last 6 months)
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_trends = Application.objects.filter(applied_at__gte=six_months_ago)\
        .annotate(month=TruncMonth('applied_at'))\
        .values('month')\
        .annotate(count=Count('id'))\
        .order_by('month')

    # 3. Students by institution
    students_by_institution = User.objects.filter(role='STUDENT').values(
        'institution__name'
    ).annotate(count=Count('id')).order_by('-count')[:8]
    
    # 4. Courses vs Internships distribution
    program_distribution = {
        'Courses': Course.objects.count(),
        'Internships': Internship.objects.count()
    }
    
    # 5. Application density by institution (Combined Course/Internship)
    # We'll do this in a clean way to avoid double counting or NULLs
    from institutions.models import Institution
    inst_apps = Institution.objects.annotate(
        app_count=Count('course__application', distinct=True) + Count('internship__application', distinct=True)
    ).values('name', 'app_count').order_by('-app_count')[:10]

    context = {
        'applications_by_status': list(applications_by_status),
        'monthly_trends': [
            {'month': item['month'].strftime('%b %Y'), 'count': item['count']} 
            for item in monthly_trends
        ],
        'students_by_institution': list(students_by_institution),
        'program_distribution': program_distribution,
        'inst_apps': list(inst_apps),
    }
    
    return render(request, 'admin/reports.html', context)


@admin_required
def student_list(request):
    """List all students"""
    students = User.objects.filter(role='STUDENT').select_related('institution')
    return render(request, 'admin/students.html', {
        'students': students
    })


@admin_required
def student_detail(request, student_id):
    """View student details"""
    from django.shortcuts import get_object_or_404
    student = get_object_or_404(User, id=student_id, role='STUDENT')
    applications = Application.objects.filter(student=student)
    return render(request, 'admin/student_detail.html', {
        'student': student,
        'applications': applications
    })


@admin_required
def admin_profile(request):
    """Admin profile page"""
    from django.contrib import messages
    
    user = request.user
    
    if request.method == 'POST':
        # Update profile
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone') or None
        user.address = request.POST.get('address') or None
        
        # Handle password change
        new_password = request.POST.get('new_password')
        if new_password:
            user.set_password(new_password)
        
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return render(request, 'admin/profile.html', {'user': user})
    
    return render(request, 'admin/profile.html', {'user': user})

