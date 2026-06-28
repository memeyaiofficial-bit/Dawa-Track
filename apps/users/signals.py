"""
Django signals for the users app.

Handles automatic creation of related objects and logging
for user lifecycle events.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.users.models import User, UserPermission


@receiver(post_save, sender=User)
def create_user_permissions(sender, instance, created, **kwargs):
    """Automatically create a UserPermission instance for new users."""
    if created:
        UserPermission.objects.get_or_create(user=instance)
