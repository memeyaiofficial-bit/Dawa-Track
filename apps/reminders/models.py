from django.db import models
from django.utils import timezone
from datetime import timedelta
from apps.users.models import User
from apps.patients.models import Patient
from apps.prescriptions.models import Prescription


class Reminder(models.Model):
    """Medication reminders sent to patients."""
    
    REMINDER_TYPE_CHOICES = [
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('push', 'Push Notification'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent Successfully'),
        ('failed', 'Failed'),
        ('delivery_failed', 'Delivery Failed'),
        ('acknowledged', 'Acknowledged by Patient'),
        ('bounce', 'Bounced'),
    ]
    
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='reminders'
    )
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='reminders')
    
    # Reminder details
    scheduled_time = models.DateTimeField(help_text='When reminder should be sent')
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPE_CHOICES)
    message_content = models.TextField(help_text='Content of the reminder message')
    
    # Delivery tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    delivery_status = models.CharField(max_length=100, blank=True)
    
    # External API tracking
    external_message_id = models.CharField(
        max_length=255,
        blank=True,
        help_text='ID from Africa\'s Talking or other gateway'
    )
    
    # Retry mechanism
    retry_count = models.IntegerField(default=0)
    last_retry_at = models.DateTimeField(null=True, blank=True)
    max_retries = models.IntegerField(default=3)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reminders'
        ordering = ['-scheduled_time']
        indexes = [
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['status', '-scheduled_time']),
            models.Index(fields=['-scheduled_time']),
        ]
    
    def __str__(self):
        return f"Reminder - {self.patient.user.email} - {self.scheduled_time}"
    
    def is_overdue(self):
        """Check if reminder is overdue (scheduled time has passed)."""
        return timezone.now() > self.scheduled_time
    
    def should_retry(self):
        """Check if reminder should be retried."""
        return (
            self.status == 'failed' and
            self.retry_count < self.max_retries and
            self.last_retry_at is None or
            timezone.now() > self.last_retry_at + timedelta(minutes=15)
        )
    
    def can_be_sent(self):
        """Check if reminder can be sent."""
        patient = self.patient
        
        # Check if patient consents to this reminder type
        consent_map = {
            'sms': patient.consent_sms,
            'whatsapp': patient.consent_whatsapp,
            'email': patient.consent_email,
        }
        
        return consent_map.get(self.reminder_type, True)
    
    def mark_as_sent(self, external_id=''):
        """Mark reminder as sent."""
        self.status = 'sent'
        self.sent_at = timezone.now()
        if external_id:
            self.external_message_id = external_id
        self.save()
    
    def mark_as_failed(self):
        """Mark reminder as failed."""
        self.status = 'failed'
        self.save()
    
    def increment_retry(self):
        """Increment retry count."""
        self.retry_count += 1
        self.last_retry_at = timezone.now()
        if self.retry_count >= self.max_retries:
            self.status = 'delivery_failed'
        self.save()
    
    @staticmethod
    def generate_reminder_message(prescription, patient):
        """Generate reminder message content."""
        return (
            f"Hi {patient.user.first_name or 'there'},\n\n"
            f"Time to take your medication:\n"
            f"💊 {prescription.drug_name} - {prescription.dosage}\n\n"
            f"Please confirm once taken by replying with 'Y' or react with ✅\n\n"
            f"Stay healthy! 💪"
        )


class ReminderTemplate(models.Model):
    """Pre-configured reminder message templates."""
    
    name = models.CharField(max_length=100)
    reminder_type = models.CharField(
        max_length=20,
        choices=Reminder.REMINDER_TYPE_CHOICES
    )
    message_template = models.TextField(
        help_text='Use {drug_name}, {dosage}, {patient_name}, {time} as placeholders'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reminder_templates'
    
    def __str__(self):
        return f"{self.name} ({self.get_reminder_type_display()})"
    
    def render(self, prescription, patient, scheduled_time):
        """Render template with actual values."""
        return self.message_template.format(
            drug_name=prescription.drug_name,
            dosage=prescription.dosage,
            patient_name=patient.user.first_name or patient.user.email,
            time=scheduled_time.strftime('%I:%M %p'),
        )


class ReminderResponse(models.Model):
    """Track patient responses to reminders."""
    
    RESPONSE_TYPE_CHOICES = [
        ('acknowledged', 'Acknowledged'),
        ('missed', 'Marked as Missed'),
        ('will_take', 'Will Take Soon'),
        ('cannot_take', 'Cannot Take'),
        ('other', 'Other'),
    ]
    
    reminder = models.OneToOneField(
        Reminder,
        on_delete=models.CASCADE,
        related_name='response'
    )
    response_type = models.CharField(
        max_length=20,
        choices=RESPONSE_TYPE_CHOICES
    )
    message = models.TextField(blank=True, help_text='Patient\'s message')
    received_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reminder_responses'
        ordering = ['-received_at']
    
    def __str__(self):
        return f"Response from {self.reminder.patient.user.email} - {self.response_type}"


class RemissionAlert(models.Model):
    """Alerts for missed doses or low adherence."""
    
    ALERT_TYPE_CHOICES = [
        ('missed_dose', 'Missed Dose'),
        ('low_adherence', 'Low Adherence'),
        ('prescription_expiring', 'Prescription Expiring'),
        ('multiple_missed', 'Multiple Missed Doses'),
    ]
    
    ALERT_LEVEL_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='dose_alerts')
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='alerts',
        null=True,
        blank=True
    )
    
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPE_CHOICES)
    alert_level = models.CharField(max_length=20, choices=ALERT_LEVEL_CHOICES, default='warning')
    message = models.TextField()
    
    # Alert recipients
    notified_doctor = models.BooleanField(default=False)
    notified_nurse = models.BooleanField(default=False)
    
    # Status
    is_resolved = models.BooleanField(default=False)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'reminder_alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient', 'is_resolved']),
            models.Index(fields=['alert_level', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.patient.user.email}"
    
    def notify_doctor(self):
        """Send notification to assigned doctor."""
        if not self.notified_doctor:
            # Will be handled by Celery task
            pass
    
    def resolve(self):
        """Mark alert as resolved."""
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.save()
