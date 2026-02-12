from django.db import models
from django.utils import timezone
from apps.users.models import User
from apps.patients.models import Patient


class PalliativeCare(models.Model):
    """Palliative/Comfort care plan for patients."""
    
    patient = models.OneToOneField(
        Patient,
        on_delete=models.CASCADE,
        related_name='palliative_care'
    )
    doctor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='palliative_patients'
    )
    
    # Diagnosis information
    primary_diagnosis = models.TextField()
    additional_diagnoses = models.TextField(blank=True)
    
    # Goals of care
    goals_of_care = models.TextField(
        help_text='Patient and family goals for treatment and care'
    )
    symptom_management_priorities = models.JSONField(
        default=list,
        help_text='Priority symptoms to manage (pain, nausea, anxiety, etc.)'
    )
    
    # Comfort care configuration
    check_in_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('twice_daily', 'Twice Daily'),
            ('every_other_day', 'Every Other Day'),
            ('three_times_weekly', '3x Weekly'),
        ],
        help_text='How often to check in with patient'
    )
    check_in_times = models.JSONField(
        default=list,
        help_text='Preferred times for check-ins'
    )
    
    # Alert settings
    missed_dose_alert_threshold = models.IntegerField(
        default=2,
        help_text='Number of missed doses to trigger alert'
    )
    alert_recipients = models.JSONField(
        default=list,
        help_text='List of staff to notify on alerts'
    )
    
    # Contact preferences
    family_contact_name = models.CharField(max_length=100, blank=True)
    family_contact_phone = models.CharField(max_length=20, blank=True)
    family_notification_preference = models.CharField(
        max_length=50,
        choices=[
            ('all_updates', 'All Updates'),
            ('critical_only', 'Critical Updates Only'),
            ('none', 'No Notifications'),
        ],
        default='all_updates'
    )
    
    # Care team coordination
    assigned_nurse = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='palliative_care_assigned'
    )
    team_members = models.JSONField(
        default=list,
        help_text='IDs of care team members (doctors, nurses, social workers)'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Notes
    special_instructions = models.TextField(blank=True)
    advance_directives = models.TextField(blank=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'palliative_care'
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['doctor']),
        ]
    
    def __str__(self):
        return f"Palliative Care - {self.patient.user.email}"
    
    def is_active_plan(self):
        """Check if palliative care plan is currently active."""
        return (
            self.is_active and
            (self.end_date is None or self.end_date >= timezone.now().date())
        )


class ComfortMedicationSchedule(models.Model):
    """Special scheduling for comfort care medications."""
    
    FREQUENCY_CHOICES = [
        ('as_needed', 'As Needed (PRN)'),
        ('every_4_hours', 'Every 4 Hours'),
        ('every_6_hours', 'Every 6 Hours'),
        ('every_8_hours', 'Every 8 Hours'),
        ('twice_daily', 'Twice Daily'),
        ('once_daily', 'Once Daily'),
        ('custom', 'Custom'),
    ]
    
    palliative_care = models.ForeignKey(
        PalliativeCare,
        on_delete=models.CASCADE,
        related_name='comfort_schedules'
    )
    
    medication_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    
    # For custom frequency
    custom_frequency_description = models.TextField(blank=True)
    
    # Instructions
    indication = models.TextField(help_text='What symptom this addresses')
    special_instructions = models.TextField(blank=True)
    
    # Priority
    is_priority = models.BooleanField(default=False, help_text='Critical medication')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'comfort_medication_schedules'
        ordering = ['-is_priority', '-created_at']
    
    def __str__(self):
        return f"{self.medication_name} - {self.palliative_care.patient.user.email}"


class PalliativeCareCheckIn(models.Model):
    """Daily/regular check-ins with palliative care patients."""
    
    PATIENT_STATUS_CHOICES = [
        ('stable', 'Stable'),
        ('declining', 'Declining'),
        ('in_pain', 'In Pain'),
        ('anxious', 'Anxious'),
        ('distressed', 'Distressed'),
        ('sleeping', 'Sleeping'),
        ('no_response', 'No Response'),
    ]
    
    palliative_care = models.ForeignKey(
        PalliativeCare,
        on_delete=models.CASCADE,
        related_name='check_ins'
    )
    
    checked_in_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role__in': ['doctor', 'nurse']}
    )
    
    check_in_time = models.DateTimeField(auto_now_add=True)
    patient_status = models.CharField(
        max_length=20,
        choices=PATIENT_STATUS_CHOICES
    )
    
    # Observations
    pain_level = models.IntegerField(
        choices=[(i, str(i)) for i in range(0, 11)],
        help_text='0-10 pain scale'
    )
    overall_assessment = models.TextField()
    observations = models.TextField(blank=True)
    interventions_taken = models.TextField(blank=True)
    
    # Follow-up
    requires_escalation = models.BooleanField(default=False)
    escalation_notes = models.TextField(blank=True)
    
    # Medication adherence for this check-in
    medications_taken_as_scheduled = models.BooleanField(default=True)
    medication_issues = models.TextField(blank=True)
    
    is_completed = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'palliative_care_checkins'
        ordering = ['-check_in_time']
        indexes = [
            models.Index(fields=['palliative_care', '-check_in_time']),
        ]
    
    def __str__(self):
        return f"Check-in - {self.palliative_care.patient.user.email} - {self.check_in_time}"


class PalliativeCareNotes(models.Model):
    """Clinical notes for palliative care patients."""
    
    NOTE_TYPE_CHOICES = [
        ('progress', 'Progress Note'),
        ('assessment', 'Assessment'),
        ('intervention', 'Intervention Note'),
        ('family_communication', 'Family Communication'),
        ('care_plan_update', 'Care Plan Update'),
    ]
    
    palliative_care = models.ForeignKey(
        PalliativeCare,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
    )
    
    note_type = models.CharField(max_length=30, choices=NOTE_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    is_shared_with_patient = models.BooleanField(default=False)
    is_shared_with_family = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'palliative_care_notes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['palliative_care', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.palliative_care.patient.user.email}"
