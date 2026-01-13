from django.db import models
from django.conf import settings


class Institution(models.Model):
    name = models.CharField(max_length=200, verbose_name='College Name')
    location = models.CharField(max_length=200)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name='College Phone')
    email = models.EmailField(blank=True, null=True, verbose_name='College Email')
    website = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='institutions/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    # Principal Information
    principal_name = models.CharField(max_length=200, blank=True, null=True, verbose_name='Principal Name')
    principal_phone = models.CharField(max_length=15, blank=True, null=True, verbose_name='Principal Phone')
    principal_email = models.EmailField(blank=True, null=True, verbose_name='Principal Email')
    
    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'COORDINATOR'},
        related_name='managed_institutions'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Institution'
        verbose_name_plural = 'Institutions'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def total_courses(self):
        return self.course_set.count()

    @property
    def total_internships(self):
        return self.internship_set.count()
    
    @property
    def assigned_coordinators(self):
        """Get all coordinators assigned to this institution through courses or internships"""
        from accounts.models import User
        coordinator_ids = set()
        # From courses
        for course in self.course_set.all():
            if course.coordinator:
                coordinator_ids.add(course.coordinator.id)
        # From internships
        for internship in self.internship_set.all():
            if internship.coordinator:
                coordinator_ids.add(internship.coordinator.id)
        # Main coordinator
        if self.coordinator:
            coordinator_ids.add(self.coordinator.id)
        return User.objects.filter(id__in=coordinator_ids)
