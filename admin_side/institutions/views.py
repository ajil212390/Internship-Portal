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
    """View company details with students and coordinators"""
    institution = get_object_or_404(Institution, id=id)
    
    # Get students belonging to this company
    students = User.objects.filter(institution=institution, role='STUDENT')
    
    # Get all coordinators assigned to this company
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
    if request.method == 'POST':
        # Get HR coordinator account details
        hr_username = request.POST.get('hr_username', '').strip()
        hr_password = request.POST.get('hr_password', '')
        hr_password_confirm = request.POST.get('hr_password_confirm', '')
        hr_name = request.POST.get('hr_coordinator_name', '').strip()
        hr_email = request.POST.get('hr_coordinator_email', '').strip()
        hr_phone = request.POST.get('hr_coordinator_phone', '').strip()
        
        # Validation
        errors = []
        if not hr_username:
            errors.append("HR Coordinator username is required")
        elif User.objects.filter(username=hr_username).exists():
            errors.append("Username already exists. Please choose a different username.")
        
        if not hr_password:
            errors.append("Password is required")
        elif len(hr_password) < 8:
            errors.append("Password must be at least 8 characters")
        elif hr_password != hr_password_confirm:
            errors.append("Passwords do not match")
        
        if not hr_name:
            errors.append("HR Coordinator name is required")
        
        if not hr_email:
            errors.append("HR Coordinator email is required")
        elif User.objects.filter(email=hr_email).exists():
            errors.append("Email already exists. Please use a different email.")
        
        if errors:
            from django.contrib import messages
            for error in errors:
                messages.error(request, error)
            return render(request, 'admin/add_institution.html', {
                'form_data': request.POST
            })
        
        # Split name into first and last name
        name_parts = hr_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Create the HR Coordinator user account
        hr_coordinator = User.objects.create_user(
            username=hr_username,
            email=hr_email,
            password=hr_password,
            first_name=first_name,
            last_name=last_name,
            role='COORDINATOR',
            phone=hr_phone or None,
            approval_status='APPROVED'
        )
        
        # Create the Institution/Company with HR coordinator assigned
        institution = Institution.objects.create(
            name=request.POST['name'],
            location=request.POST['location'],
            email=request.POST.get('email') or None,
            phone=request.POST.get('phone') or None,
            hr_coordinator_name=hr_name,
            hr_coordinator_phone=hr_phone or None,
            hr_coordinator_email=hr_email,
            coordinator=hr_coordinator  # Assign the created coordinator
        )
        
        # Also set the institution for the coordinator
        hr_coordinator.institution = institution
        hr_coordinator.save()
        
        from django.contrib import messages
        messages.success(request, f'Company "{institution.name}" and HR Coordinator "{hr_username}" created successfully!')
        return redirect('institution_list')

    return render(request, 'admin/add_institution.html', {})

@admin_required
def edit_institution(request, id):
    institution = get_object_or_404(Institution, id=id)

    if request.method == 'POST':
        institution.name = request.POST['name']
        institution.location = request.POST['location']
        institution.email = request.POST.get('email') or None
        institution.phone = request.POST.get('phone') or None
        institution.hr_coordinator_name = request.POST.get('hr_coordinator_name') or None
        institution.hr_coordinator_phone = request.POST.get('hr_coordinator_phone') or None
        institution.hr_coordinator_email = request.POST.get('hr_coordinator_email') or None
        institution.save()
        from django.contrib import messages
        messages.success(request, f'Company "{institution.name}" updated successfully!')
        return redirect('institution_list')

    return render(request, 'admin/edit_institution.html', {
        'institution': institution,
    })

@admin_required
def delete_institution(request, id):
    institution = get_object_or_404(Institution, id=id)
    institution.delete()
    return redirect('institution_list')

@admin_required
def toggle_institution_status(request, id):
    """Toggle company active/inactive status"""
    institution = get_object_or_404(Institution, id=id)
    institution.is_active = not institution.is_active
    institution.save()
    return redirect('institution_list')

