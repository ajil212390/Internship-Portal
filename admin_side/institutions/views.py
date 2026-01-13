from django.shortcuts import render, redirect, get_object_or_404
from accounts.decorators import admin_required
from .models import Institution
from accounts.models import User

@admin_required
def institution_list(request):
    institutions = Institution.objects.all()
    return render(request, 'admin/institutions.html', {
        'institutions': institutions
    })

@admin_required
def institution_detail(request, id):
    """View institution details with students and coordinators"""
    institution = get_object_or_404(Institution, id=id)
    
    # Get students belonging to this institution
    students = User.objects.filter(institution=institution, role='STUDENT')
    
    # Get all coordinators assigned to this institution
    coordinators = institution.assigned_coordinators
    
    # Get courses and internships for this institution
    courses = institution.course_set.all()
    internships = institution.internship_set.all()
    
    return render(request, 'admin/institution_detail.html', {
        'institution': institution,
        'students': students,
        'coordinators': coordinators,
        'courses': courses,
        'internships': internships,
    })

@admin_required
def add_institution(request):
    coordinators = User.objects.filter(role='COORDINATOR')

    if request.method == 'POST':
        Institution.objects.create(
            name=request.POST['name'],
            location=request.POST['location'],
            email=request.POST.get('email') or None,
            phone=request.POST.get('phone') or None,
            principal_name=request.POST.get('principal_name') or None,
            principal_phone=request.POST.get('principal_phone') or None,
            principal_email=request.POST.get('principal_email') or None,
            coordinator_id=request.POST.get('coordinator') or None
        )
        return redirect('institution_list')

    return render(request, 'admin/add_institution.html', {
        'coordinators': coordinators
    })

@admin_required
def edit_institution(request, id):
    institution = get_object_or_404(Institution, id=id)
    coordinators = User.objects.filter(role='COORDINATOR')

    if request.method == 'POST':
        institution.name = request.POST['name']
        institution.location = request.POST['location']
        institution.email = request.POST.get('email') or None
        institution.phone = request.POST.get('phone') or None
        institution.principal_name = request.POST.get('principal_name') or None
        institution.principal_phone = request.POST.get('principal_phone') or None
        institution.principal_email = request.POST.get('principal_email') or None
        institution.coordinator_id = request.POST.get('coordinator') or None
        institution.save()
        return redirect('institution_list')

    return render(request, 'admin/edit_institution.html', {
        'institution': institution,
        'coordinators': coordinators
    })

@admin_required
def delete_institution(request, id):
    institution = get_object_or_404(Institution, id=id)
    institution.delete()
    return redirect('institution_list')

@admin_required
def toggle_institution_status(request, id):
    """Toggle institution active/inactive status"""
    institution = get_object_or_404(Institution, id=id)
    institution.is_active = not institution.is_active
    institution.save()
    return redirect('institution_list')

