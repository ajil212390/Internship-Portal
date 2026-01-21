from django.db import models
from django.conf import settings
from courses.models import Course
from internships.models import Internship


class Application(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('WITHDRAWN', 'Withdrawn'),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'STUDENT'},
        related_name='applications'
    )
    course = models.ForeignKey(Course, null=True, blank=True, on_delete=models.CASCADE)
    internship = models.ForeignKey(Internship, null=True, blank=True, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications'
    )
    notes = models.TextField(blank=True, null=True, help_text="Notes from reviewer")
    student_remarks = models.TextField(blank=True, null=True, help_text="Remarks from student")

    class Meta:
        verbose_name = 'Application'
        verbose_name_plural = 'Applications'
        ordering = ['-applied_at']

    def __str__(self):
        program = self.course.name if self.course else self.internship.title if self.internship else 'N/A'
        return f"{self.student.username} - {program} ({self.status})"

    @property
    def program_name(self):
        if self.course:
            return self.course.name
        elif self.internship:
            return self.internship.title
        return 'N/A'

    @property
    def program_type(self):
        if self.course:
            return 'Course'
        elif self.internship:
            return 'Internship'
        return 'N/A'
