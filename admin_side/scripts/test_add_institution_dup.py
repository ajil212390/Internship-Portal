from django.test import Client
from accounts.models import User
from institutions.models import Institution

c = Client()
admin = User.objects.filter(role='ADMIN').first() or User.objects.filter(is_superuser=True).first()
print('Admin:', admin.username)
if not admin:
    print('No admin')
else:
    c.force_login(admin)
    resp = c.post('/admin/institutions/add/', {
        'name':'TestCo_Dup',
        'location':'DupLoc',
        'email':'dup@example.com',
        'phone':'000',
        'hr_username':'hr_test_post',  # existing username
        'hr_password':'AaBbCc123',
        'hr_password_confirm':'AaBbCc123',
        'hr_coordinator_name':'Dup HR',
        'hr_coordinator_email':'dup_hr@example.com',
        'hr_coordinator_phone':'000111222'
    }, HTTP_HOST='127.0.0.1', follow=True)
    print('Status', resp.status_code)
    content = resp.content.decode('utf-8')
    print('Contains name value:', 'value="TestCo_Dup"' in content)
    print('Contains hr_username value:', 'value="hr_test_post"' in content)
    print('Contains error message:', 'Username already exists' in content)
