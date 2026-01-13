from django.db import models
from django.conf import settings


class Batch(models.Model):
    """
    Batch model representing a group of students.
    One batch can have multiple coordinators assigned.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    institution = models.ForeignKey(
        'institutions.Institution',
        on_delete=models.CASCADE,
        related_name='batches'
    )
    coordinators = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        limit_choices_to={'role': 'COORDINATOR'},
        related_name='assigned_batches',
        blank=True,
        help_text='Coordinators assigned to this batch'
    )
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    max_students = models.IntegerField(default=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Batch'
        verbose_name_plural = 'Batches'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.institution.name}"

    @property
    def student_count(self):
        """Count of students in this batch"""
        from accounts.models import User
        return User.objects.filter(batch=self, role='STUDENT').count()

    @property
    def available_seats(self):
        """Available seats in this batch"""
        return self.max_students - self.student_count

    @property
    def coordinator_names(self):
        """Get comma-separated list of coordinator names"""
        return ", ".join([c.get_full_name() or c.username for c in self.coordinators.all()])
