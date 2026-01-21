from django.db import models
from django.conf import settings
from institutions.models import Institution


class Course(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'COORDINATOR'},
        related_name='coordinated_courses'
    )
    CATEGORY_CHOICES = (
        ('WEB', 'Web Development'),
        ('PYTHON', 'Python Programming'),
        ('DATA', 'Data Science'),
        ('AI', 'Artificial Intelligence'),
        ('APP', 'App Development'),
        ('CYBER', 'Cyber Security'),
        ('DESIGN', 'UI/UX Design'),
        ('OTHER', 'Other'),
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='OTHER')
    duration_days = models.IntegerField(default=30, help_text="Duration in days")
    max_students = models.IntegerField(default=50)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    eligibility = models.TextField(blank=True, null=True, help_text="Eligibility criteria")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.institution.name}"

    @property
    def enrolled_count(self):
        return self.application_set.filter(status='APPROVED').count()

    @property
    def available_seats(self):
        return self.max_students - self.enrolled_count
