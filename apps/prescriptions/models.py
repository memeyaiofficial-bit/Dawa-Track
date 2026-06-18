from django.db import models
# 1. Added MaxValueValidator to the import statement below
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from apps.users.models import User
from apps.patients.models import Patient


class Prescription(models.Model):
    """Medication prescription model."""
    
    FREQUENCY_CHOICES = [
        ('once_daily', 'Once Daily'),
        ('twice_daily', 'Twice Daily'),
        ('thrice_daily', 'Three Times Daily'),
        ('four_times_daily', 'Four Times Daily'),
        ('custom', 'Custom Schedule'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='prescriptions_authored'
    )
    
    # Drug information
    drug_name = models.CharField(max_length=200)
    drug_code = models.CharField(max_length=50, blank=True, help_text='Pharmacological code or ID')
    dosage = models.CharField(max_length=100, help_text='e.g., 500mg, 2 tablets')
    
    # Frequency
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    custom_frequency_description = models.TextField(
        blank=True,
        help_text='Description for custom frequency (e.g., "Morning after breakfast, Evening before bed")'
    )
    
    # Duration
    duration_days = models.IntegerField(validators=[MinValueValidator(1)])
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Additional information
    indication = models.TextField(blank=True, help_text='Why this drug is prescribed')
    notes = models.TextField(blank=True, help_text='Special instructions')
    
    # Palliative care flag
    is_comfort_medication = models.BooleanField(
        default=False,
        help_text='Mark as comfort care medication in palliative care'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='prescriptions_created'
    )
    
    class Meta:
        db_table = 'prescriptions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient', 'is_active']),
            models.Index(fields=['end_date']),
            models.Index(fields=['doctor']),
        ]
    
    def __str__(self):
        return f"{self.drug_name} - {self.patient.user.email}"
    
    def save(self, *args, **kwargs):
        """Auto-set end_date based on start_date and duration."""
        if self.start_date and self.duration_days:
            from datetime import timedelta
            self.end_date = self.start_date + timedelta(days=self.duration_days)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if prescription has ended."""
        return self.end_date < timezone.now().date()
    
    def get_frequency_count(self):
        """Return number of doses per day."""
        freq_map = {
            'once_daily': 1,
            'twice_daily': 2,
            'thrice_daily': 3,
            'four_times_daily': 4,
        }
        return freq_map.get(self.frequency, self.schedule_times.count())
    
    def get_total_doses(self):
        """Calculate total number of doses for this prescription."""
        return self.get_frequency_count() * self.duration_days
    
    def get_scheduled_times(self):
        """Get all scheduled times for this prescription."""
        return self.schedule_times.all().order_by('scheduled_time')


class PrescriptionSchedule(models.Model):
    """Specific times for medication doses."""
    
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='schedule_times'
    )
    scheduled_time = models.TimeField(help_text='e.g., 08:00 for 8 AM')
    description = models.CharField(
        max_length=100,
        blank=True,
        help_text='e.g., "Morning with breakfast"'
    )
    day_index = models.IntegerField(
        null=True,
        blank=True,
        # 2. Replaced models.functions.Max(6) with MaxValueValidator(6) below
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        help_text='0-6 for days of week (0=Monday). Leave blank for daily.'
    )
    
    class Meta:
        db_table = 'prescription_schedules'
        ordering = ['scheduled_time']
        unique_together = ['prescription', 'scheduled_time', 'day_index']
    
    def __str__(self):
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        day = f" ({day_names[self.day_index]})" if self.day_index is not None else ""
        return f"{self.prescription.drug_name} - {self.scheduled_time}{day}"


class DoseLog(models.Model):
    """Track individual dose intakes (adherence tracking)."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('taken', 'Taken'),
        ('missed', 'Missed'),
        ('skipped', 'Skipped'),
        ('partially_taken', 'Partially Taken'),
    ]
    
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='dose_logs'
    )
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='dose_logs')
    
    # Timing
    scheduled_time = models.DateTimeField(help_text='When dose was scheduled')
    actual_intake_time = models.DateTimeField(null=True, blank=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, help_text='Why dose was missed or notes')
    
    # Verification
    confirmed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Nurse or staff who verified the dose'
    )
    confirmation_method = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ('patient_reported', 'Patient Reported'),
            ('sms_confirmed', 'SMS Confirmation'),
            ('whatsapp_confirmed', 'WhatsApp Confirmation'),
            ('nurse_verified', 'Nurse Verified'),
        ]
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dose_logs'
        ordering = ['-scheduled_time']
        indexes = [
            models.Index(fields=['patient', '-scheduled_time']),
            models.Index(fields=['prescription', 'status']),
            models.Index(fields=['status', '-scheduled_time']),
        ]
    
    def __str__(self):
        return f"{self.patient.user.email} - {self.prescription.drug_name} - {self.scheduled_time}"
    
    def mark_as_taken(self):
        """Mark dose as taken."""
        self.status = 'taken'
        self.actual_intake_time = timezone.now()
        self.save()
    
    def mark_as_missed(self, notes=''):
        """Mark dose as missed."""
        self.status = 'missed'
        self.notes = notes
        self.save()
    
    def is_overdue(self):
        """Check if dose is overdue."""
        from datetime import timedelta
        grace_period = 2  # hours
        return (
            self.status == 'pending' and
            timezone.now() > self.scheduled_time + timedelta(hours=grace_period)
        )


class PrescriptionChange(models.Model):
    """Audit trail for prescription modifications."""
    
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('suspended', 'Suspended'),
        ('resumed', 'Resumed'),
        ('discontinued', 'Discontinued'),
    ]
    
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='change_history'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    reason = models.TextField(blank=True)
