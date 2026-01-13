from django.db import models
from django.conf import settings
from applications.models import Application


class Attendance(models.Model):
    """
    Attendance model with MORNING and EVENING sessions.
    Each day can have two attendance records per student - one for each session.
    """
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
        ('EXCUSED', 'Excused'),
    ]
    
    SESSION_CHOICES = [
        ('MORNING', 'Morning'),
        ('EVENING', 'Evening'),
    ]

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    date = models.DateField()
    session = models.CharField(
        max_length=10, 
        choices=SESSION_CHOICES, 
        default='MORNING',
        help_text='Session: MORNING or EVENING'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PRESENT')
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marked_attendance'
    )
    marked_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)
    check_in_time = models.TimeField(blank=True, null=True)
    check_out_time = models.TimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendance Records'
        ordering = ['-date', '-session']
        # Unique constraint: one record per application, date, and session
        unique_together = ['application', 'date', 'session']

    def __str__(self):
        return f"{self.application.student.username} - {self.date} - {self.session} - {self.status}"

    @property
    def student(self):
        return self.application.student

    @property
    def program_name(self):
        return self.application.program_name
    
    @classmethod
    def get_attendance_percentage(cls, application):
        """
        Calculate attendance percentage for an application.
        Counts PRESENT and LATE as attended.
        """
        records = cls.objects.filter(application=application)
        total = records.count()
        if total == 0:
            return 0.0
        
        attended = records.filter(status__in=['PRESENT', 'LATE']).count()
        return round((attended / total) * 100, 2)
    
    @classmethod
    def is_eligible_for_certificate(cls, application):
        """
        Check if student is eligible for certificate (≥75% attendance).
        Only applicable for approved enrollments.
        """
        if application.status != 'APPROVED':
            return False
        
        percentage = cls.get_attendance_percentage(application)
        return percentage >= 75.0
