from django.db import models
from applications.models import Application

class Certificate(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE)
    approved = models.BooleanField(default=False)
    approved_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.application.student_name
