from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class User(AbstractUser):
    objects = UserManager()  # Ensure create_user works as expected
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('COORDINATOR', 'HR Coordinator'),
        ('STUDENT', 'Student'),
    )
    APPROVAL_STATUS_CHOICES = (
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    QUALIFICATION_CHOICES = (
        ('10TH', '10th Standard'),
        ('12TH', '12th Standard'),
        ('HIGH_SCHOOL', 'High School'),
        ('DIPLOMA', 'Diploma'),
        ('UG', 'Under Graduate (UG)'),
        ('PG', 'Post Graduate (PG)'),
        ('PHD', 'PhD'),
        ('OTHER', 'Other'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')
    phone = models.CharField(max_length=15, blank=True, null=True)
    highest_qualification = models.CharField(max_length=20, choices=QUALIFICATION_CHOICES, blank=True, null=True)
    highest_qualification_other = models.CharField(max_length=100, blank=True, null=True, help_text='Custom qualification if Other is selected')
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    institution = models.ForeignKey(
        'institutions.Institution',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    is_active = models.BooleanField(default=True)
    # Approval workflow fields
    approval_status = models.CharField(
        max_length=20, 
        choices=APPROVAL_STATUS_CHOICES, 
        default='APPROVED',  # Default to APPROVED for admin/coordinator, will be PENDING for students
        help_text='Approval status for student registrations'
    )
    approved_by = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_students',
        help_text='Coordinator or Admin who approved/rejected this user'
    )
    approval_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True, help_text='Reason for rejection if rejected')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
