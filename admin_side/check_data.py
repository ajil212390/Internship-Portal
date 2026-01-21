import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_internship.settings')
django.setup()

from accounts.models import User
from applications.models import Application
from courses.models import Course
from institutions.models import Institution

print("--- GLOBAL DATA ---")
print("Total Students:", User.objects.filter(role='STUDENT').count())
print("Approved Students:", User.objects.filter(role='STUDENT', approval_status='APPROVED').count())

inst_name = 'vidhya' # Name from the image
inst = Institution.objects.filter(name__icontains=inst_name).first()

if inst:
    print(f"\n--- INSTITUTION: {inst.name} (ID: {inst.id}) ---")
    students = User.objects.filter(institution=inst, role='STUDENT')
    print(f"Total Students: {students.count()}")
    print(f"Approved Students: {students.filter(approval_status='APPROVED').count()}")
    
    courses = Course.objects.filter(institution=inst)
    print(f"Total Courses: {courses.count()}")
    for c in courses:
        apps = Application.objects.filter(course=c)
        print(f"Course: {c.name} (ID: {c.id}) - Apps: {apps.count()} (Approved: {apps.filter(status='APPROVED').count()})")
        for app in apps:
            print(f"  - App by {app.student.username}: Status={app.status}, Student Approved={app.student.approval_status}")
else:
    print(f"\nInstitution '{inst_name}' not found.")
    print("Available Institutions:")
    for i in Institution.objects.all():
        print(f"- {i.name} (ID: {i.id})")
