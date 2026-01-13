from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def admin_required(view_func):
    """Decorator to require admin role"""
    return user_passes_test(
        lambda u: u.is_authenticated and (u.is_superuser or u.role == 'ADMIN'),
        login_url='/login/'
    )(view_func)


def coordinator_required(view_func):
    """Decorator to require coordinator role"""
    return user_passes_test(
        lambda u: u.is_authenticated and u.role == 'COORDINATOR',
        login_url='/login/'
    )(view_func)


def student_required(view_func):
    """
    Decorator to require student role AND approval.
    Only approved students can access student pages.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/login/')
        
        if request.user.role != 'STUDENT':
            return redirect('/login/')
        
        # Check if student is approved
        if request.user.approval_status != 'APPROVED':
            messages.error(request, 'Your account is pending approval or has been rejected.')
            return redirect('/login/')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def approved_student_required(view_func):
    """
    Decorator to require an APPROVED student.
    Blocks students who are pending approval or rejected.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/login/')
        
        if request.user.role != 'STUDENT':
            messages.error(request, 'This page is only for students.')
            return redirect('/login/')
        
        if request.user.approval_status == 'PENDING':
            messages.warning(request, 'Your account is pending approval. Please wait for coordinator approval.')
            return redirect('/login/')
        
        if request.user.approval_status == 'REJECTED':
            rejection_reason = request.user.rejection_reason or 'No reason provided'
            messages.error(request, f'Your registration was rejected. Reason: {rejection_reason}')
            return redirect('/login/')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(*allowed_roles):
    """Decorator to require any of the specified roles"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('/login/')
            if request.user.is_superuser or request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            return redirect('/login/')
        return wrapper
    return decorator
