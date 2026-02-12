from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.users.models import User


class Patient(models.Model):
    """Patient profile model."""
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    CARE_CATEGORY_CHOICES = [
        ('normal', 'Normal Care'),
        ('palliative', 'Palliative Care'),
    ]
    
    BLOOD_TYPE_CHOICES = [
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPE_CHOICES, blank=True)
    
    # Care classification
    care_category = models.CharField(
        max_length=20,
        choices=CARE_CATEGORY_CHOICES,
        default='normal',
        help_text='Normal: Regular patient, Palliative: End-of-life or comfort care'
    )
    
    # Contact information
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    
    # Medical information
    medical_history = models.TextField(blank=True, help_text='History of major illnesses')
    current_conditions = models.TextField(blank=True, help_text='Chronic conditions')
    allergies = models.TextField(blank=True, help_text='Drug allergies and reactions')
    
    # Doctor assignment
    assigned_doctor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='patients_as_doctor',
        limit_choices_to={'role': 'doctor'}
    )
    assigned_nurse = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='patients_as_nurse',
        limit_choices_to={'role': 'nurse'}
    )
    
    # Preference settings
    preferred_reminder_channel = models.CharField(
        max_length=20,
        choices=[
            ('sms', 'SMS'),
            ('whatsapp', 'WhatsApp'),
            ('email', 'Email'),
            ('all', 'All Channels'),
        ],
        default='whatsapp'
    )
    reminder_time_preference = models.TimeField(
        default='08:00',
        help_text='Preferred time to receive reminders'
    )
    
    # Consent flags
    consent_sms = models.BooleanField(default=True, help_text='Patient consents to SMS reminders')
    consent_whatsapp = models.BooleanField(default=True, help_text='Patient consents to WhatsApp')
    consent_email = models.BooleanField(default=True, help_text='Patient consents to Email')
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'patients'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['care_category']),
            models.Index(fields=['assigned_doctor']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_care_category_display()}"
    
    @property
    def age(self):
        """Calculate patient age."""
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def get_active_prescriptions(self):
        """Get all active prescriptions for this patient."""
        from apps.prescriptions.models import Prescription
        return Prescription.objects.filter(
            patient=self,
            is_active=True,
            end_date__gte=models.functions.Now()
        )
    
    def get_adherence_rate(self, days=30):
        """Calculate medication adherence rate for last N days."""
        from django.utils import timezone
        from datetime import timedelta
        from apps.prescriptions.models import DoseLog
        
        start_date = timezone.now() - timedelta(days=days)
        
        logs = DoseLog.objects.filter(
            patient=self,
            created_at__gte=start_date
        )
        
        if not logs.exists():
            return 0
        
        taken_count = logs.filter(status='taken').count()
        total_count = logs.count()
        
        return (taken_count / total_count * 100) if total_count > 0 else 0


class PatientContactLog(models.Model):
    """Track patient communications."""
    
    CONTACT_TYPE_CHOICES = [
        ('phone', 'Phone Call'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('visit', 'In-person Visit'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='contact_logs')
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPE_CHOICES)
    contacted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'patient_contact_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['patient', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.patient.user.email} - {self.get_contact_type_display()}"
