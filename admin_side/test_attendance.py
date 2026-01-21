
import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_internship.settings')
django.setup()

from applications.models import Application
from attendance.models import Attendance
from accounts.models import User

def test_mark():
    # Get a coordinator
    coord = User.objects.filter(role='COORDINATOR').first()
    if not coord:
        print("No coordinator found")
        return

    # Get an approved application for this coordinator
    app = Application.objects.filter(status='APPROVED').first()
    if not app:
        print("No approved applications found")
        return

    print(f"Testing marking attendance for {app.student.username} by {coord.username}")
    
    date = timezone.now().date()
    session = 'MORNING'
    
    try:
        attendance, created = Attendance.objects.update_or_create(
            application=app,
            date=date,
            session=session,
            defaults={
                'status': 'PRESENT',
                'marked_by': coord
            }
        )
        print(f"Success! Attendance {'created' if created else 'updated'}. Status: {attendance.status}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_mark()
