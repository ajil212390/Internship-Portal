from django.shortcuts import render
from accounts.decorators import admin_required
from .models import Application

@admin_required
def application_list(request):
    applications = Application.objects.all()
    return render(request, 'admin/applications.html', {
        'applications': applications
    })
