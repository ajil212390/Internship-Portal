from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Application


@receiver(post_save, sender=Application)
def create_certificate_on_approval(sender, instance, created, **kwargs):
    """When an Application is approved, ensure a Certificate record exists (approved=False).

    This runs for approvals made via admin or any view.
    """
    if instance.status == 'approved':
        try:
            # import here to avoid circular import at module load
            from certificates.models import Certificate
        except Exception:
            return

        Certificate.objects.get_or_create(application=instance, defaults={'approved': False})
