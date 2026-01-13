from django.shortcuts import render, get_object_or_404, redirect
from accounts.decorators import admin_required
from .models import Course
from accounts.models import User
from institutions.models import Institution

@admin_required
def course_list(request):
    courses = Course.objects.all()
    return render(request, 'admin/courses.html', {
        'courses': courses
    })

@admin_required
def add_course(request):
    institutions = Institution.objects.filter(is_active=True)
    coordinators = User.objects.filter(role='COORDINATOR')
    
    if request.method == 'POST':
        Course.objects.create(
            name=request.POST['name'],
            description=request.POST.get('description') or None,
            institution_id=request.POST['institution'],
            coordinator_id=request.POST.get('coordinator') or None,
            duration_days=request.POST.get('duration_days') or 30,
            max_students=request.POST.get('max_students') or 50,
        )
        return redirect('course_list')
    
    return render(request, 'admin/add_course.html', {
        'institutions': institutions,
        'coordinators': coordinators
    })

@admin_required
def edit_course(request, id):
    course = get_object_or_404(Course, id=id)
    institutions = Institution.objects.filter(is_active=True)
    coordinators = User.objects.filter(role='COORDINATOR')
    
    if request.method == 'POST':
        course.name = request.POST['name']
        course.description = request.POST.get('description') or None
        course.institution_id = request.POST['institution']
        course.coordinator_id = request.POST.get('coordinator') or None
        course.duration_days = request.POST.get('duration_days') or 30
        course.max_students = request.POST.get('max_students') or 50
        course.save()
        return redirect('course_list')
    
    return render(request, 'admin/edit_course.html', {
        'course': course,
        'institutions': institutions,
        'coordinators': coordinators
    })

@admin_required
def delete_course(request, id):
    course = get_object_or_404(Course, id=id)
    course.delete()
    return redirect('course_list')

@admin_required
def assign_course_coordinator(request, id):
    course = get_object_or_404(Course, id=id)
    coordinators = User.objects.filter(role='COORDINATOR')

    if request.method == 'POST':
        course.coordinator_id = request.POST.get('coordinator')
        course.save()
        return redirect('course_list')

    return render(request, 'admin/assign_course_coordinator.html', {
        'course': course,
        'coordinators': coordinators
    })
