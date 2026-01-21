from django.test import Client
from accounts.models import User
from institutions.models import Institution

c=Client()
admin=User.objects.filter(role='ADMIN').first() or User.objects.filter(is_superuser=True).first()
coord=User.objects.create_user(username='temp_coord2', email='tcoord2@example.com', password='pass123456', role='COORDINATOR', approval_status='APPROVED')
print('Admin exists:', bool(admin))
# Coordinator tries
c.force_login(coord)
resp=c.post('/admin/institutions/add/', {'name':'BadAttempt','location':'X','hr_username':'badhr','hr_password':'P@ssw0rd','hr_password_confirm':'P@ssw0rd','hr_coordinator_name':'B','hr_coordinator_email':'b@example.com'}, HTTP_HOST='127.0.0.1', follow=True)
print('Coord post status:', resp.status_code)
print('Coord redirects:', resp.redirect_chain)
print('You must be an Admin msg present:', 'You must be an Admin' in resp.content.decode('utf-8'))
# Admin tries
c.logout()
if admin:
    c.force_login(admin)
    resp2=c.post('/admin/institutions/add/', {'name':'GoodInstTEST','location':'Town','hr_username':'hr_good2','hr_password':'GoodPass123','hr_password_confirm':'GoodPass123','hr_coordinator_name':'Good HR','hr_coordinator_email':'hr_good2@example.com'}, HTTP_HOST='127.0.0.1', follow=True)
    print('Admin post status:', resp2.status_code)
    print('GoodInst created:', Institution.objects.filter(name__icontains='GoodInstTEST').exists())
else:
    print('No admin to test')