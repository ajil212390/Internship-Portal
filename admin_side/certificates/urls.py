from django.urls import path
from .views import (
    certificate_list,
    certificate_detail,
    generate_certificate,
    approve_certificate,
    generate_certificates_view,
    issue_certificate,
    revoke_certificate,
    eligible_students,
    regenerate_certificate,
    delete_certificate
)

urlpatterns = [
    path('admin/certificates/', certificate_list, name='certificate_list'),
    path('admin/certificates/<int:certificate_id>/', certificate_detail, name='certificate_detail'),
    path('admin/certificates/generate/<int:application_id>/', generate_certificate, name='generate_certificate'),
    path('admin/certificates/approve/<int:certificate_id>/', approve_certificate, name='approve_certificate'),
    path('admin/certificates/issue/<int:certificate_id>/', issue_certificate, name='issue_certificate'),
    path('admin/certificates/revoke/<int:certificate_id>/', revoke_certificate, name='revoke_certificate'),
    path('generate/', generate_certificates_view, name='generate_certs'),
    path('admin/certificates/eligible/', eligible_students, name='eligible_students'),
    path('admin/certificates/regenerate/<int:certificate_id>/', regenerate_certificate, name='regenerate_certificate'),
    path('admin/certificates/delete/<int:certificate_id>/', delete_certificate, name='delete_certificate'),
]