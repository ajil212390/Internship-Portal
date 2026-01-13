from django.db import models
from datetime import date
from programs.models import Program
from accounts.models import User


class Attendance(models.Model):
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'}, null=True, blank=True
    )
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    date = models.DateField(default=date.today)
    status = models.CharField(
        max_length=10,
        choices=[('present', 'Present'), ('absent', 'Absent'), ('late', 'Late')]
    )

    class Meta:
        unique_together = ('student', 'program', 'date')

    def __str__(self):
        if self.student:
            student_repr = self.student.username
        else:
            student_repr = 'Unknown'
        return f"{student_repr} - {self.date} - {self.status}"

