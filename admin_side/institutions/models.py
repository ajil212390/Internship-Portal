from django.db import models
from django.conf import settings


class Institution(models.Model):
    """Company model - represents partner companies that offer internships/courses"""
    name = models.CharField(max_length=200, verbose_name='Company Name')
    location = models.CharField(max_length=200)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name='Company Phone')
    email = models.EmailField(blank=True, null=True, verbose_name='Company Email')
    website = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='companies/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    # HR Coordinator Information (contact person at the company)
    hr_coordinator_name = models.CharField(max_length=200, blank=True, null=True, verbose_name='HR Coordinator Name')
    hr_coordinator_phone = models.CharField(max_length=15, blank=True, null=True, verbose_name='HR Coordinator Phone')
    hr_coordinator_email = models.EmailField(blank=True, null=True, verbose_name='HR Coordinator Email')
    
    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'COORDINATOR'},
        related_name='managed_companies'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
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
        """Get all coordinators assigned to this company through various relations"""
        from accounts.models import User
        coordinator_ids = set()
        
        # 1. Coordinators who have this institution as their primary institution
        inst_coordinators = User.objects.filter(institution=self, role='COORDINATOR')
        for coord in inst_coordinators:
            coordinator_ids.add(coord.id)
            
        # 2. Coordinators assigned to courses of this company
        for course in self.course_set.all():
            if course.coordinator:
                coordinator_ids.add(course.coordinator.id)
                
        # 3. Coordinators assigned to internships of this company
        for internship in self.internship_set.all():
            if internship.coordinator:
                coordinator_ids.add(internship.coordinator.id)
                
        # 4. The main coordinator stored directly on the institution
        if self.coordinator:
            coordinator_ids.add(self.coordinator.id)
            
        return User.objects.filter(id__in=coordinator_ids)
