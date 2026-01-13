from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count

from accounts.decorators import admin_required
from accounts.models import User
from institutions.models import Institution
from .models import Batch


@admin_required
def batch_list(request):
    """List all batches"""
    batches = Batch.objects.select_related('institution').prefetch_related('coordinators')
    
    # Filters
    institution_filter = request.GET.get('institution', '')
    status_filter = request.GET.get('status', '')
    
    if institution_filter:
        batches = batches.filter(institution_id=institution_filter)
    if status_filter == 'active':
        batches = batches.filter(is_active=True)
    elif status_filter == 'inactive':
        batches = batches.filter(is_active=False)
    
    institutions = Institution.objects.filter(is_active=True)
    
    context = {
        'batches': batches,
        'institutions': institutions,
        'institution_filter': institution_filter,
        'status_filter': status_filter,
    }
    return render(request, 'admin/batches.html', context)


@admin_required
def batch_add(request):
    """Add a new batch"""
    institutions = Institution.objects.filter(is_active=True)
    coordinators = User.objects.filter(role='COORDINATOR', is_active=True)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        institution_id = request.POST.get('institution')
        start_date = request.POST.get('start_date') or None
        end_date = request.POST.get('end_date') or None
        max_students = request.POST.get('max_students', 50)
        coordinator_ids = request.POST.getlist('coordinators')
        
        # Validation
        if Batch.objects.filter(name=name).exists():
            messages.error(request, 'A batch with this name already exists.')
            return render(request, 'admin/add_batch.html', {
                'institutions': institutions,
                'coordinators': coordinators,
                'form_data': request.POST,
            })
        
        # Create batch
        batch = Batch.objects.create(
            name=name,
            description=description,
            institution_id=institution_id,
            start_date=start_date,
            end_date=end_date,
            max_students=int(max_students) if max_students else 50,
        )
        
        # Assign coordinators
        if coordinator_ids:
            batch.coordinators.set(coordinator_ids)
        
        messages.success(request, f'Batch "{name}" created successfully!')
        return redirect('batches:list')
    
    context = {
        'institutions': institutions,
        'coordinators': coordinators,
    }
    return render(request, 'admin/add_batch.html', context)


@admin_required
def batch_detail(request, batch_id):
    """View batch details"""
    batch = get_object_or_404(Batch.objects.select_related('institution').prefetch_related('coordinators'), id=batch_id)
    
    # Get students in this batch
    students = User.objects.filter(batch=batch, role='STUDENT').order_by('-created_at')
    
    # Stats
    pending_students = students.filter(approval_status='PENDING').count()
    approved_students = students.filter(approval_status='APPROVED').count()
    
    context = {
        'batch': batch,
        'students': students,
        'pending_students': pending_students,
        'approved_students': approved_students,
    }
    return render(request, 'admin/batch_detail.html', context)


@admin_required
def batch_edit(request, batch_id):
    """Edit a batch"""
    batch = get_object_or_404(Batch, id=batch_id)
    institutions = Institution.objects.filter(is_active=True)
    coordinators = User.objects.filter(role='COORDINATOR', is_active=True)
    
    if request.method == 'POST':
        batch.name = request.POST.get('name', batch.name)
        batch.description = request.POST.get('description', '')
        batch.institution_id = request.POST.get('institution', batch.institution_id)
        batch.start_date = request.POST.get('start_date') or None
        batch.end_date = request.POST.get('end_date') or None
        batch.max_students = int(request.POST.get('max_students', 50))
        batch.is_active = request.POST.get('is_active') == 'on'
        batch.save()
        
        # Update coordinators
        coordinator_ids = request.POST.getlist('coordinators')
        batch.coordinators.set(coordinator_ids)
        
        messages.success(request, f'Batch "{batch.name}" updated successfully!')
        return redirect('batches:detail', batch_id=batch.id)
    
    context = {
        'batch': batch,
        'institutions': institutions,
        'coordinators': coordinators,
    }
    return render(request, 'admin/edit_batch.html', context)


@admin_required
def batch_delete(request, batch_id):
    """Delete a batch"""
    batch = get_object_or_404(Batch, id=batch_id)
    
    if request.method == 'POST':
        name = batch.name
        batch.delete()
        messages.success(request, f'Batch "{name}" deleted successfully!')
        return redirect('batches:list')
    
    return render(request, 'admin/confirm_delete_batch.html', {'batch': batch})


@admin_required
def batch_students(request, batch_id):
    """View and manage students in a batch"""
    batch = get_object_or_404(Batch.objects.select_related('institution'), id=batch_id)
    
    status_filter = request.GET.get('status', 'all')
    students = User.objects.filter(batch=batch, role='STUDENT').order_by('-created_at')
    
    if status_filter == 'pending':
        students = students.filter(approval_status='PENDING')
    elif status_filter == 'approved':
        students = students.filter(approval_status='APPROVED')
    elif status_filter == 'rejected':
        students = students.filter(approval_status='REJECTED')
    
    context = {
        'batch': batch,
        'students': students,
        'status_filter': status_filter,
    }
    return render(request, 'admin/batch_students.html', context)
