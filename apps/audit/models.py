"""
Models for the audit app.

Provides audit logging for tracking user activities,
data changes, and compliance requirements.
"""
from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    """Central audit log for tracking all significant events across the system."""

    ACTION_CHOICES = [
        ('user_created', 'User Created'),
        ('user_updated', 'User Updated'),
        ('user_deleted', 'User Deleted'),
        ('login', 'Login'),
        ('login_failed', 'Login Failed'),
        ('logout', 'Logout'),
        ('password_change', 'Password Changed'),
        ('data_export', 'Data Exported'),
        ('report_generated', 'Report Generated'),
        ('settings_changed', 'Settings Changed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    resource_type = models.CharField(max_length=50, blank=True, help_text="Type of resource affected")
    resource_id = models.CharField(max_length=50, blank=True, help_text="ID of resource affected")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        return f"{self.user.email if self.user else 'anonymous'} - {self.action} at {self.timestamp}"
