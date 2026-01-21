from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from accounts.decorators import admin_required
from .models import Attendance
from applications.models import Application


@admin_required
def attendance_list(request):
    """List all attendance records"""
    attendance_records = Attendance.objects.select_related(
        'application__student', 'application__course', 'application__internship', 'marked_by'
    ).all()
    return render(request, 'admin/attendance.html', {
        'attendance_records': attendance_records
    })


@admin_required
def attendance_by_application(request, application_id):
    """View attendance for a specific application"""
    application = get_object_or_404(Application, id=application_id)
    attendance_records = Attendance.objects.filter(application=application).order_by('-date')
    return render(request, 'admin/attendance_detail.html', {
        'application': application,
        'attendance_records': attendance_records
    })


@admin_required
def mark_attendance(request, application_id):
    """Mark attendance for a student"""
    application = get_object_or_404(Application, id=application_id, status='APPROVED')
    
    if request.method == 'POST':
        date = request.POST.get('date')
        session = request.POST.get('session', 'MORNING')
        status = request.POST.get('status', 'PRESENT')
        remarks = request.POST.get('remarks', '')
        
        if not date:
            messages.error(request, 'Please select a date.')
            return redirect('attendance_by_application', application_id=application_id)
        
        # Date locking logic
        try:
            today = timezone.now().date()
            mark_date = timezone.datetime.strptime(date, '%Y-%m-%d').date()
            if mark_date < today:
                messages.error(request, 'Attendance marking for past dates is locked.')
                return redirect('attendance_by_application', application_id=application_id)
        except (ValueError, TypeError):
            pass # Fallback to Django's own validation if strptime fails
        
        if session not in ['MORNING', 'EVENING']:
            messages.error(request, 'Invalid session type.')
            return redirect('attendance_by_application', application_id=application_id)
        
        try:
            attendance, created = Attendance.objects.update_or_create(
                application=application,
                date=date,
                session=session,
                defaults={
                    'status': status,
                    'remarks': remarks,
                    'marked_by': request.user
                }
            )
            action = 'created' if created else 'updated'
            messages.success(request, f'Attendance {action} successfully for {date} ({session})')
        except Exception as e:
            messages.error(request, f'Error marking attendance: {str(e)}')
        
        return redirect('attendance_by_application', application_id=application_id)
    
    return render(request, 'admin/mark_attendance.html', {
        'application': application,
        'today': timezone.now().date(),
        'status_choices': Attendance.STATUS_CHOICES,
        'session_choices': Attendance.SESSION_CHOICES,
    })


@admin_required
def attendance_report(request):
    """Generate attendance report"""
    from django.db.models import Count, Q
    
    # Get attendance summary by application
    applications = Application.objects.filter(status='APPROVED').annotate(
        total_present=Count('attendance_records', filter=Q(attendance_records__status='PRESENT')),
        total_absent=Count('attendance_records', filter=Q(attendance_records__status='ABSENT')),
        total_late=Count('attendance_records', filter=Q(attendance_records__status='LATE')),
        total_excused=Count('attendance_records', filter=Q(attendance_records__status='EXCUSED')),
    )
    
    return render(request, 'admin/attendance_report.html', {
        'applications': applications
    })
