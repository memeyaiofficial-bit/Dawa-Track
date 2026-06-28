"""
Django signals for the audit app.

Automatically logs key model events for audit trail.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from apps.users.models import AuditLog

User = get_user_model()


@receiver(post_save, sender=User)
def log_user_save(sender, instance, created, **kwargs):
    """Log user creation and updates."""
    action = 'user_created' if created else 'user_updated'
    AuditLog.objects.create(
        user=instance,
        action=action,
        ip_address=None,
        success=True,
    )
