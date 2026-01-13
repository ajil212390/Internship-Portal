from django.db import models
from django.contrib.auth.models import User

# 1. Extends the built-in login system
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    college = models.CharField(max_length=255)
    course = models.CharField(max_length=100)
    location = models.CharField(max_length=100)

# 2. Data for students to search
class InternshipProgram(models.Model):
    title = models.CharField(max_length=200)
    institution_name = models.CharField(max_length=255)
    location = models.CharField(max_length=100)
    description = models.TextField()

# 3. Data for "Track Application Status"
class StudentApplication(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
    ]
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    program = models.ForeignKey(InternshipProgram, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='Pending') # Pending, Approved, Completed

# 4. Data for "View Attendance"
class Attendance(models.Model):
    application = models.ForeignKey(StudentApplication, on_delete=models.CASCADE)
    date = models.DateField()
    is_present = models.BooleanField(default=False)