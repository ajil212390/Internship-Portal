from django.db import models
from django.conf import settings
from django.utils import timezone


class Certificate(models.Model):
    """
    Certificate model for tracking generated certificates.
    Eligibility: Enrollment approved + Attendance ≥75%
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('ISSUED', 'Issued'),
        ('REVOKED', 'Revoked'),
    ]
    
    application = models.OneToOneField(
        'applications.Application',
        on_delete=models.CASCADE,
        related_name='certificate'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    is_eligible = models.BooleanField(default=False)
    attendance_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        help_text='Attendance percentage at the time of certificate generation'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_certificates'
    )
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issued_certificates',
        help_text='Admin who issued this certificate'
    )
    issued_date = models.DateField(null=True, blank=True)
    certificate_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Certificate'
        verbose_name_plural = 'Certificates'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Certificate for {self.application.student.username} - {self.application.program_name}"
    
    def calculate_eligibility(self):
        """
        Calculate if student is eligible for certificate.
        Requirements:
        1. Application/Enrollment must be APPROVED
        2. Attendance percentage must be ≥75%
        """
        from attendance.models import Attendance
        
        # Check if enrollment is approved
        if self.application.status != 'APPROVED':
            self.is_eligible = False
            self.attendance_percentage = 0
            return False
        
        # Calculate attendance percentage
        self.attendance_percentage = Attendance.get_attendance_percentage(self.application)
        self.is_eligible = self.attendance_percentage >= 75
        
        return self.is_eligible
    
    def generate_certificate_number(self):
        """Generate a unique certificate number"""
        import random
        import string
        
        prefix = "CERT"
        year = timezone.now().year
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        self.certificate_number = f"{prefix}-{year}-{self.application.id}-{random_part}"
        return self.certificate_number
    
    def issue(self, issued_by_user):
        """Issue the certificate"""
        if not self.is_eligible:
            self.calculate_eligibility()
        
        if self.is_eligible:
            self.status = 'ISSUED'
            self.issued_by = issued_by_user
            self.issued_date = timezone.now().date()
            if not self.certificate_number:
                self.generate_certificate_number()
            self.save()
            return True
        return False
    
    @property
    def can_download(self):
        """Check if certificate can be downloaded by student"""
        return self.status == 'ISSUED' and self.is_eligible
    
    @property
    def student(self):
        return self.application.student
    
    @property
    def program_name(self):
        return self.application.program_name


class CertificateTemplate(models.Model):
    name = models.CharField(max_length=100)
    # The blank certificate image
    background_image = models.ImageField(upload_to='cert_templates/')
    
    # Coordinates where the Name will be printed
    name_x_axis = models.IntegerField(default=400, help_text="X Coordinate (Horizontal)")
    name_y_axis = models.IntegerField(default=300, help_text="Y Coordinate (Vertical)")
    
    # Font size for the name
    font_size = models.IntegerField(default=30)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name