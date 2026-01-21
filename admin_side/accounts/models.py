from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
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
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    institution = models.ForeignKey(
        'institutions.Institution',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    qualification = models.CharField(max_length=255, blank=True, null=True, help_text="Student's highest qualification")
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
