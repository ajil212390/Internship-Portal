from django.shortcuts import render, get_object_or_404, redirect
from accounts.decorators import admin_required
from .models import Internship
from accounts.models import User
from institutions.models import Institution

@admin_required
def internship_list(request):
    internships = Internship.objects.all()
    return render(request, 'admin/internships.html', {
        'internships': internships
    })

@admin_required
def add_internship(request):
    institutions = Institution.objects.filter(is_active=True)
    coordinators = User.objects.filter(role='COORDINATOR')
    
    if request.method == 'POST':
        Internship.objects.create(
            title=request.POST['title'],
            description=request.POST.get('description') or None,
            institution_id=request.POST['institution'],
            coordinator_id=request.POST.get('coordinator') or None,
            duration=request.POST.get('duration') or 30,
            max_students=request.POST.get('max_students') or 20,
            requirements=request.POST.get('requirements') or None,
            skills_gained=request.POST.get('skills_gained') or None,
        )
        return redirect('internship_list')
    
    return render(request, 'admin/add_internship.html', {
        'institutions': institutions,
        'coordinators': coordinators
    })

@admin_required
def edit_internship(request, id):
    internship = get_object_or_404(Internship, id=id)
    institutions = Institution.objects.filter(is_active=True)
    coordinators = User.objects.filter(role='COORDINATOR')
    
    if request.method == 'POST':
        internship.title = request.POST['title']
        internship.description = request.POST.get('description') or None
        internship.institution_id = request.POST['institution']
        internship.coordinator_id = request.POST.get('coordinator') or None
        internship.duration = request.POST.get('duration') or 30
        internship.max_students = request.POST.get('max_students') or 20
        internship.requirements = request.POST.get('requirements') or None
        internship.skills_gained = request.POST.get('skills_gained') or None
        internship.save()
        return redirect('internship_list')
    
    return render(request, 'admin/edit_internship.html', {
        'internship': internship,
        'institutions': institutions,
        'coordinators': coordinators
    })

@admin_required
def delete_internship(request, id):
    internship = get_object_or_404(Internship, id=id)
    internship.delete()
    return redirect('internship_list')

@admin_required
def assign_internship_coordinator(request, id):
    internship = get_object_or_404(Internship, id=id)
    coordinators = User.objects.filter(role='COORDINATOR')

    if request.method == 'POST':
        internship.coordinator_id = request.POST.get('coordinator')
        internship.save()
        return redirect('internship_list')

    return render(request, 'admin/assign_internship_coordinator.html', {
        'internship': internship,
        'coordinators': coordinators
    })
