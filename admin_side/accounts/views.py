from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from accounts.decorators import admin_required
from .models import User
from institutions.models import Institution


def unified_login(request):
    """Unified login for all roles: Student, Coordinator, Admin"""
    # If already logged in, redirect based on role
    if request.user.is_authenticated:
        return redirect_by_role(request.user)
    
    next_url = request.POST.get('next') or request.GET.get('next')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        selected_role = request.POST.get('role', 'STUDENT')
        
        user = authenticate(request, username=username, password=password)
        
        if user:
            # Check if user's actual role matches selected login role
            if user.is_superuser:
                # Superuser can login under any role, default to admin
                login(request, user)
                return redirect(next_url or '/admin/dashboard/')
            elif user.role == selected_role:
                # For students, check approval status
                if user.role == 'STUDENT':
                    if user.approval_status == 'PENDING':
                        return render(request, 'admin/login.html', {
                            'error': 'Your registration is pending approval. Please wait for coordinator approval.',
                            'warning': True
                        })
                    elif user.approval_status == 'REJECTED':
                        rejection_msg = user.rejection_reason or 'No reason provided'
                        return render(request, 'admin/login.html', {
                            'error': f'Your registration was rejected. Reason: {rejection_msg}',
                            'danger': True
                        })
                
                login(request, user)
                return redirect(next_url or get_dashboard_url(user.role))
            else:
                # Role mismatch
                role_display = dict(User.ROLE_CHOICES).get(user.role, user.role)
                return render(request, 'admin/login.html', {
                    'error': f'Your account is registered as {role_display}. Please select the correct role tab.'
                })
        else:
            return render(request, 'admin/login.html', {
                'error': 'Invalid username or password'
            })
    
    # Check for success message from registration
    success = request.GET.get('registered')
    context = {}
    if success:
        context['success'] = 'Registration successful! Your account is pending approval by a coordinator.'
    
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
    """Student registration view with institution and batch selection, pending approval"""
    if request.user.is_authenticated:
        return redirect_by_role(request.user)
    
    # Get all active institutions and batches for the dropdowns
    institutions = Institution.objects.filter(is_active=True)
    from batches.models import Batch
    batches = Batch.objects.filter(is_active=True).select_related('institution')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        phone = request.POST.get('phone', '')
        institution_id = request.POST.get('institution', '')
        batch_id = request.POST.get('batch', '')
        
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
        
        if not institution_id:
            errors.append('Please select an institution')
        
        if errors:
            return render(request, 'student/register.html', {
                'errors': errors,
                'form_data': request.POST,
                'institutions': institutions,
                'batches': batches,
            })
        
        # Create user with pending approval status
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone or None,
            role='STUDENT',
            approval_status='PENDING',  # Pending coordinator approval
            institution_id=institution_id,
            batch_id=batch_id if batch_id else None,
        )
        
        return redirect('/login/?registered=1')
    
    return render(request, 'student/register.html', {
        'institutions': institutions,
        'batches': batches,
    })


# Keep backward compatibility - admin_login now uses unified_login
def admin_login(request):
    return unified_login(request)


def admin_logout(request):
    logout(request)
    return redirect('/login/')


@admin_required
def coordinator_list(request):
    coordinators = User.objects.filter(role='COORDINATOR').select_related('institution')
    return render(request, 'admin/coordinators.html', {
        'coordinators': coordinators
    })

@admin_required
def add_coordinator(request):
    institutions = Institution.objects.filter(is_active=True)
    
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
        return redirect('coordinator_list')

    return render(request, 'admin/add_coordinator.html', {
        'institutions': institutions
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
