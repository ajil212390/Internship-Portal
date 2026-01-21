
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_internship.settings')
django.setup()

from django.db import models
from accounts.models import User
from applications.models import Application
from attendance.models import Attendance
from courses.models import Course
from internships.models import Internship

try:
    print(f"Total Users: {User.objects.count()}")
    print(f"Students: {User.objects.filter(role='STUDENT').count()}")
    print(f"Coordinators: {User.objects.filter(role='COORDINATOR').count()}")
    print(f"Approved Applications: {Application.objects.filter(status='APPROVED').count()}")
    print(f"Total Attendance Records: {Attendance.objects.count()}")

    # Check coordinator assignments
    for coord in User.objects.filter(role='COORDINATOR'):
        courses = Course.objects.filter(coordinator=coord)
        internships = Internship.objects.filter(coordinator=coord)
        print(f"Coordinator {coord.username} (Institution: {coord.institution}): {courses.count()} courses, {internships.count()} internships")
        
        # Check if they have approved applications for their programs
        apps = Application.objects.filter(
            (models.Q(course__in=courses) | models.Q(internship__in=internships)),
            status='APPROVED'
        )
        print(f"  Approved apps for this coordinator: {apps.count()}")
        
        if apps.count() == 0:
            # Check if there are any applications for these programs at all
            all_apps = Application.objects.filter(
                (models.Q(course__in=courses) | models.Q(internship__in=internships))
            )
            print(f"  Total apps (all statuses) for this coordinator: {all_apps.count()}")
            if all_apps.exists():
                print(f"  Statuses: {[a.status for a in all_apps]}")

except Exception as e:
    print(f"Error: {e}")
