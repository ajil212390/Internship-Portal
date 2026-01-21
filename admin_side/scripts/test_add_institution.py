from django.test import Client
from accounts.models import User
from institutions.models import Institution

c = Client()
admin = User.objects.filter(role='ADMIN').first() or User.objects.filter(is_superuser=True).first()
print('Admin found:', getattr(admin, 'username', None))
if not admin:
    print('No admin user found. Exiting.')
else:
    c.force_login(admin)
    # Test adding via admin-side custom view
    resp = c.post('/admin/institutions/add/', {
        'name': 'TestCo_Post',
        'location': 'TestLoc',
        'email': 'testco_post@example.com',
        'phone': '1234567890',
        'hr_username': 'hr_test_post',
        'hr_password': 'TestPass123',
        'hr_password_confirm': 'TestPass123',
        'hr_coordinator_name': 'HR Tester',
        'hr_coordinator_email': 'hr_test_post@example.com',
        'hr_coordinator_phone': '9876543210'
    }, HTTP_HOST='127.0.0.1', follow=True)
    print('Custom view created count:', Institution.objects.filter(name__icontains='TestCo_Post').count())

    # Test adding via Django admin site
    resp2 = c.post('/admin/institutions/institution/add/', {
        'name': 'TestCo_Admin',
        'location': 'AdminLoc',
        'email': 'testco_admin@example.com',
        'phone': '1112223333',
        '_save': 'Save'
    }, HTTP_HOST='127.0.0.1', follow=True)
    print('Admin add status:', resp2.status_code)
    # Check for redirect to change list
    print('Admin add redirects:', resp2.redirect_chain)
    print('Admin added count:', Institution.objects.filter(name__icontains='TestCo_Admin').count())
    print('Status code:', resp.status_code)
    print('Redirects:', resp.redirect_chain)
    print('Content length:', len(resp.content))
    print('Success text present:', b'created successfully' in resp.content)
    print('Institution count:', Institution.objects.filter(name__icontains='TestCo_Post').count())