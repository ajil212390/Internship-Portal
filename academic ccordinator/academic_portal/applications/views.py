from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Application


def application_list(request):
	"""List applications and allow approving/rejecting them via POST.

	POST params:
	  - application_id: id of the Application
	  - action: 'approve' or 'reject'
	"""
	if request.method == 'POST':
		app_id = request.POST.get('application_id')
		action = request.POST.get('action')
		if app_id and action in ('approve', 'reject'):
			try:
				app = Application.objects.get(id=app_id)
				app.status = 'approved' if action == 'approve' else 'rejected'
				app.save()
				messages.success(request, f"Application for {app.student_name} set to {app.status}.")
			except Application.DoesNotExist:
				messages.error(request, "Application not found.")
		else:
			messages.error(request, "Invalid request.")

		return redirect('applications:application_list')

	applications = Application.objects.all().order_by('-applied_on')
	return render(request, 'applications/list.html', {'applications': applications})
