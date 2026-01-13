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
    for inst in Institution.objects.order_by('-created_at')[:3]:
        recent_activities.append({
            'date': inst.created_at,
            'name': inst.name,
            'type': 'Institution',
            'status': 'Active' if inst.is_active else 'Inactive',
            'icon': 'building',
            'url': f'/admin/institutions/{inst.id}/'
        })
    
    # Recent coordinators
    for coord in User.objects.filter(role='COORDINATOR').order_by('-created_at')[:3]:
        recent_activities.append({
            'date': coord.created_at,
            'name': coord.username,
            'type': 'Coordinator',
            'status': 'Active' if coord.is_active else 'Inactive',
            'icon': 'user-tie',
            'url': f'/admin/coordinators/edit/{coord.id}/'
        })
    
    # Recent courses
    for course in Course.objects.order_by('-created_at')[:3]:
        recent_activities.append({
            'date': course.created_at,
            'name': course.name,
            'type': 'Course',
            'status': 'Active' if course.is_active else 'Inactive',
            'icon': 'book',
            'url': f'/admin/courses/edit/{course.id}/'
        })
    
    # Recent internships
    for internship in Internship.objects.order_by('-created_at')[:3]:
        recent_activities.append({
            'date': internship.created_at,
            'name': internship.title,
            'type': 'Internship',
            'status': 'Active' if internship.is_active else 'Inactive',
            'icon': 'briefcase',
            'url': f'/admin/internships/edit/{internship.id}/'
        })
    
    # Sort by date descending and take top 10
    recent_activities = sorted(recent_activities, key=lambda x: x['date'], reverse=True)[:10]
    
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
    """Reports and analytics view"""
    from django.db.models import Count, Q
    from django.db.models.functions import TruncMonth
    
    # Applications by status
    applications_by_status = Application.objects.values('status').annotate(
        count=Count('id')
    )
    
    # Applications by institution
    applications_by_institution = Application.objects.values(
        'course__institution__name', 'internship__institution__name'
    ).annotate(count=Count('id'))
    
    # Students by institution
    students_by_institution = User.objects.filter(role='STUDENT').values(
        'institution__name'
    ).annotate(count=Count('id'))
    
    # Courses by institution
    courses_by_institution = Course.objects.values(
        'institution__name'
    ).annotate(count=Count('id'))
    
    context = {
        'applications_by_status': applications_by_status,
        'applications_by_institution': applications_by_institution,
        'students_by_institution': students_by_institution,
        'courses_by_institution': courses_by_institution,
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

