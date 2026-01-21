from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from accounts.decorators import admin_required
from .models import User
from institutions.models import Institution


def unified_login(request):
    """Truly role-based login: Detects role after authentication and redirects accordingly"""
    # If already logged in, redirect based on role
    if request.user.is_authenticated:
        return redirect_by_role(request.user)
    
    next_url = request.POST.get('next') or request.GET.get('next')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user:
            # Log the user in
            login(request, user)
            
            # Redirect based on actual user role
            if next_url:
                return redirect(next_url)
            return redirect_by_role(user)
        else:
            return render(request, 'admin/login.html', {
                'error': 'Invalid username or password',
                'danger': True
            })
    
    # Check for success message from registration
    success = request.GET.get('registered')
    context = {}
    if success:
        context['success'] = 'Registration successful! Login with Username and Password.'
    
    # Also handle messages passed via Django messages framework
    from django.contrib import messages
    storage = messages.get_messages(request)
    for message in storage:
        if message.tags == 'error':
            context['error'] = str(message)
            context['danger'] = True
        elif message.tags == 'success':
            context['success'] = str(message)
        elif message.tags == 'warning':
            context['error'] = str(message)
            context['warning'] = True
    
    return render(request, 'admin/login.html', context)


def redirect_by_role(user):
    """Redirect user to appropriate dashboard based on role"""
    if user.is_superuser or user.role == 'ADMIN':
        return redirect('/admin/dashboard/')
    elif user.role == 'COORDINATOR':
        return redirect('/coordinator/dashboard/')
    else:
        return redirect('/student/dashboard/')


def get_dashboard_url(role):
    """Get dashboard URL for a given role"""
    urls = {
        'ADMIN': '/admin/dashboard/',
        'COORDINATOR': '/coordinator/dashboard/',
        'STUDENT': '/student/dashboard/'
    }
    return urls.get(role, '/student/dashboard/')


def user_logout(request):
    """Logout and redirect to login page"""
    logout(request)
    return redirect('login')


def student_register(request):
    """Student Registration Completed Use Username and Password to Login"""
    if request.user.is_authenticated:
        return redirect_by_role(request.user)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        phone = request.POST.get('phone', '')
        highest_qualification = request.POST.get('highest_qualification', '')
        highest_qualification_other = request.POST.get('highest_qualification_other', '')

        
        # Validation
        errors = []
        
        if User.objects.filter(username=username).exists():
            errors.append('Username already exists')
        
        if User.objects.filter(email=email).exists():
            errors.append('Email already registered')
        
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        if len(password) < 6:
            errors.append('Password must be at least 6 characters')
        

        
        if errors:
            return render(request, 'student/register.html', {
                'errors': errors,
                'form_data': request.POST,
            })
        
        # Create user with pending approval status
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone or None,
            highest_qualification=highest_qualification or None,
            highest_qualification_other=highest_qualification_other if highest_qualification == 'OTHER' else None,
            role='STUDENT',
            approval_status='APPROVED',  # Automatically approved
            institution_id=None,
        )
        
        return redirect('/login/?registered=1')
    
    return render(request, 'student/register.html')


# Keep backward compatibility - admin_login now uses unified_login
def admin_login(request):
    return unified_login(request)


def admin_logout(request):
    logout(request)
    return redirect('/login/')


@admin_required
def coordinator_list(request):
    coordinators = User.objects.filter(role='COORDINATOR').select_related('institution')
    companies = Institution.objects.all().order_by('name')
    return render(request, 'admin/coordinators.html', {
        'coordinators': coordinators,
        'companies': companies
    })

@admin_required
def add_coordinator(request):
    institutions = Institution.objects.filter(is_active=True)
    selected_inst_id = request.GET.get('institution')
    
    if request.method == 'POST':
        user = User.objects.create_user(
            username=request.POST['username'],
            email=request.POST['email'],
            password=request.POST['password'],
            role='COORDINATOR',
            phone=request.POST.get('phone') or None,
        )
        # Assign institution if selected
        institution_id = request.POST.get('institution')
        if institution_id:
            user.institution_id = institution_id
            user.save()
            # If we came from an institution page, redirect back there
            if request.POST.get('from_institution'):
                from django.contrib import messages
                messages.success(request, f'Coordinator "{user.username}" added successfully!')
                return redirect('edit_institution', id=institution_id)
                
        return redirect('coordinator_list')

    return render(request, 'admin/add_coordinator.html', {
        'institutions': institutions,
        'selected_inst_id': selected_inst_id
    })

@admin_required
def edit_coordinator(request, id):
    coordinator = get_object_or_404(User, id=id, role='COORDINATOR')
    institutions = Institution.objects.filter(is_active=True)
    
    if request.method == 'POST':
        coordinator.username = request.POST['username']
        coordinator.email = request.POST['email']
        coordinator.phone = request.POST.get('phone') or None
        
        # Update password if provided
        new_password = request.POST.get('password')
        if new_password:
            coordinator.set_password(new_password)
        
        # Update institution
        institution_id = request.POST.get('institution')
        coordinator.institution_id = institution_id if institution_id else None
        
        coordinator.save()
        return redirect('coordinator_list')
    
    return render(request, 'admin/edit_coordinator.html', {
        'coordinator': coordinator,
        'institutions': institutions
    })

@admin_required
def delete_coordinator(request, id):
    coordinator = get_object_or_404(User, id=id, role='COORDINATOR')
    coordinator.delete()
    return redirect('coordinator_list')

# API endpoint to get coordinators by institution
@admin_required  
def get_coordinators_by_institution(request, institution_id):
    """Returns JSON list of coordinators for a specific institution"""
    coordinators = User.objects.filter(
        role='COORDINATOR',
        institution_id=institution_id,
        is_active=True
    ).values('id', 'username', 'email')
    
    return JsonResponse({
        'coordinators': list(coordinators)
    })
