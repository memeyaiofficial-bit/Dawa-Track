from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator, MinLengthValidator

class CustomUserManager(BaseUserManager):
    """Custom user manager for DawaTrack."""
    
    def create_user(self, email, password=None, role='patient', **extra_fields):
        """Create and save a regular user."""
        if not email:
            raise ValueError('Email is required')
        
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Extended User model with roles."""
    
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('patient', 'Patient'),
    ]
    
    email = models.EmailField(unique=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message='Phone number must be between 9 and 15 digits.'
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        help_text="Patient's phone number for SMS/WhatsApp reminders"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
    
    # Profile completeness
    profile_completed = models.BooleanField(default=False)
    
    # Audit fields
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_doctor(self):
        return self.role == 'doctor'
    
    def is_nurse(self):
        return self.role == 'nurse'
    
    def is_patient(self):
        return self.role == 'patient'
    
    def lock_account(self):
        """Lock account after failed login attempts."""
        self.is_locked = True
        self.save()
    
    def unlock_account(self):
        """Unlock account and reset failed attempts."""
        self.is_locked = False
        self.failed_login_attempts = 0
        self.save()
    
    def increment_failed_login(self):
        """Increment failed login counter and lock if threshold reached."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.lock_account()
        else:
            self.save()
    
    def reset_login_attempts(self):
        """Reset failed login attempts on successful login."""
        self.failed_login_attempts = 0
        self.save()


class UserPermission(models.Model):
    """Custom permissions for granular access control."""
    
    PERMISSION_CHOICES = [
        ('view_patient_data', 'Can view patient data'),
        ('edit_patient_data', 'Can edit patient data'),
        ('create_prescription', 'Can create prescriptions'),
        ('edit_prescription', 'Can edit prescriptions'),
        ('delete_prescription', 'Can delete prescriptions'),
        ('view_reports', 'Can view reports'),
        ('export_data', 'Can export data'),
        ('manage_users', 'Can manage users'),
        ('view_audit_logs', 'Can view audit logs'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='custom_permissions')
    permissions = models.JSONField(default=list, help_text="List of permission slugs")
    
    class Meta:
        db_table = 'user_permissions'
    
    def has_permission(self, permission_slug):
        """Check if user has a specific permission."""
        return permission_slug in self.permissions
    
    def add_permission(self, permission_slug):
        """Add a permission to user."""
        if permission_slug not in self.permissions:
            self.permissions.append(permission_slug)
            self.save()
    
    def remove_permission(self, permission_slug):
        """Remove a permission from user."""
        if permission_slug in self.permissions:
            self.permissions.remove(permission_slug)
            self.save()
    
    def __str__(self):
        return f"Permissions for {self.user.email}"


class AuditLog(models.Model):
    """Track user activities for security and compliance."""
    
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('login_failed', 'Failed Login'),
        ('password_change', 'Password Changed'),
        ('profile_update', 'Profile Updated'),
        ('account_locked', 'Account Locked'),
        ('account_unlocked', 'Account Unlocked'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    ip_address = models.GenericIPAddressField()
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
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.action} at {self.timestamp}"
