from django.db import models

class Program(models.Model):
    PROGRAM_TYPE = (
        ('course', 'Course'),
        ('internship', 'Internship'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    # Price in the project's default currency
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text='Numeric price for the program')
    # Duration as human-readable string (e.g., '10 weeks', '3 months')
    duration = models.CharField(max_length=100, blank=True, help_text='Duration (e.g. "10 weeks")')
    program_type = models.CharField(max_length=20, choices=PROGRAM_TYPE)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title
