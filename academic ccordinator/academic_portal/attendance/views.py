from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from applications.models import Application
from programs.models import Program
from django.contrib.auth import get_user_model
from .models import Attendance


User = get_user_model()


def mark_attendance(request):
	"""Show approved applicants and save attendance per chosen date.

	- GET: show approved students for a chosen program and date
	- POST: save attendance records for submitted students (creates or updates)
	"""
	program_id = request.GET.get('program')
	date_str = request.GET.get('date') or request.POST.get('date')
	programs = Program.objects.filter(is_active=True)

	if program_id:
		try:
			program = Program.objects.get(id=program_id)
		except Program.DoesNotExist:
			program = None
	else:
		program = None

	# Only approved applications count as enrolled
	apps_qs = Application.objects.filter(status='approved')
	if program:
		apps_qs = apps_qs.filter(program=program)

	# parse date (default to today)
	if date_str:
		try:
			mark_date = timezone.datetime.fromisoformat(date_str).date()
		except Exception:
			mark_date = timezone.now().date()
	else:
		mark_date = timezone.now().date()

	if request.method == 'POST':
		saved = 0
		for app in apps_qs:
			key = f'attendance_{app.id}'
			status = request.POST.get(key)
			if status:
				# try to resolve a User by email (if users exist)
				student_user = User.objects.filter(email__iexact=app.email).first()
				obj, created = Attendance.objects.update_or_create(
					student=student_user,
					program=app.program,
					date=mark_date,
					defaults={'status': status},
				)
				saved += 1

		messages.success(request, f'Saved {saved} attendance records.')
		# redirect to avoid duplicate POST on refresh
		params = ''
		if program:
			params = f'?program={program.id}&date={mark_date.isoformat()}'
		else:
			params = f'?date={mark_date.isoformat()}'
		return redirect(f'{request.path}{params}')

	return render(request, 'attendance/mark.html', {
		'programs': programs,
		'selected_program': program,
		'applications': apps_qs,
		'mark_date': mark_date,
	})


def student_attendance(request, app_id):
	"""View and edit a single student's attendance records.

	- GET: show attendance list for that student (by Application)
	- POST: update an existing attendance or add a new record for a date
	"""
	try:
		app = Application.objects.get(id=app_id)
	except Application.DoesNotExist:
		return redirect('attendance:mark_attendance')

	# try to resolve a User by email
	student_user = User.objects.filter(email__iexact=app.email).first()

	if student_user:
		records = Attendance.objects.filter(student=student_user).order_by('-date')
	else:
		# fallback: show any attendance entries for the same program with no linked user
		records = Attendance.objects.filter(program=app.program, student__isnull=True).order_by('-date')

	if request.method == 'POST':
		# update existing record
		if 'attendance_id' in request.POST and 'status' in request.POST:
			aid = request.POST.get('attendance_id')
			status = request.POST.get('status')
			try:
				rec = Attendance.objects.get(id=int(aid))
				rec.status = status
				rec.save()
				messages.success(request, 'Attendance updated.')
			except Attendance.DoesNotExist:
				messages.error(request, 'Record not found.')
			return redirect('attendance:student_attendance', app_id=app_id)

		# add new record for date
		new_date = request.POST.get('new_date')
		new_status = request.POST.get('new_status')
		if new_date and new_status:
			student = student_user if student_user else None
			Attendance.objects.update_or_create(
				student=student,
				program=app.program,
				date=new_date,
				defaults={'status': new_status},
			)
			messages.success(request, 'New attendance record saved.')
			return redirect('attendance:student_attendance', app_id=app_id)

	return render(request, 'attendance/student_detail.html', {
		'application': app,
		'records': records,
	})
