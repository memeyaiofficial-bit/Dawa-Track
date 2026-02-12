"""
Celery tasks for async reminder and notification jobs.
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.contrib.task_metadata import TaskMetadata
from apps.reminders.models import Reminder, RemissionAlert
from apps.prescriptions.models import DoseLog, Prescription
from apps.patients.models import Patient
from apps.reminders.integrations.africa_talking import gateway as at_gateway

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_sms_reminder(self, reminder_id):
    """
    Send SMS reminder to patient.
    
    Args:
        reminder_id: ID of the Reminder object
    """
    try:
        reminder = Reminder.objects.get(id=reminder_id)
        
        # Check if patient consents to SMS
        if not reminder.patient.consent_sms:
            logger.info(f"Patient {reminder.patient.user.email} declined SMS reminders")
            reminder.status = 'failed'
            reminder.delivery_status = 'Patient declined SMS'
            reminder.save()
            return
        
        # Get patient phone
        phone = reminder.patient.user.phone_number
        if not phone:
            logger.warning(f"No phone number for patient {reminder.patient.user.email}")
            reminder.status = 'failed'
            reminder.delivery_status = 'No phone number on file'
            reminder.save()
            return
        
        # Ensure international format
        if not phone.startswith('+'):
            phone = '+' + phone
        
        # Send via Africa's Talking
        result = at_gateway.send_sms(
            phone_number=phone,
            message=reminder.message_content
        )
        
        if result['success']:
            reminder.mark_as_sent(result.get('message_id', ''))
            reminder.delivery_status = 'SMS Sent Successfully'
            logger.info(f"SMS sent to {phone} - Message ID: {result.get('message_id')}")
        else:
            reminder.increment_retry()
            reminder.delivery_status = result.get('error', 'SMS delivery failed')
            logger.error(f"Failed to send SMS to {phone}: {result['error']}")
            
            # Retry if under max attempts
            if reminder.should_retry():
                self.retry(countdown=300)  # Retry after 5 minutes
        
        reminder.save()
    
    except Reminder.DoesNotExist:
        logger.error(f"Reminder {reminder_id} not found")
    except Exception as exc:
        logger.error(f"Error sending SMS reminder: {str(exc)}")
        self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=3)
def send_whatsapp_reminder(self, reminder_id):
    """
    Send WhatsApp reminder to patient.
    
    Args:
        reminder_id: ID of the Reminder object
    """
    try:
        reminder = Reminder.objects.get(id=reminder_id)
        
        # Check consent
        if not reminder.patient.consent_whatsapp:
            logger.info(f"Patient {reminder.patient.user.email} declined WhatsApp reminders")
            reminder.status = 'failed'
            reminder.delivery_status = 'Patient declined WhatsApp'
            reminder.save()
            return
        
        phone = reminder.patient.user.phone_number
        if not phone:
            logger.warning(f"No phone number for patient {reminder.patient.user.email}")
            reminder.status = 'failed'
            reminder.delivery_status = 'No phone number on file'
            reminder.save()
            return
        
        if not phone.startswith('+'):
            phone = '+' + phone
        
        # Send via Africa's Talking
        result = at_gateway.send_whatsapp(
            phone_number=phone,
            message=reminder.message_content
        )
        
        if result['success']:
            reminder.mark_as_sent(result.get('message_id', ''))
            reminder.delivery_status = 'WhatsApp Sent Successfully'
            logger.info(f"WhatsApp sent to {phone}")
        else:
            reminder.increment_retry()
            reminder.delivery_status = result.get('error', 'WhatsApp delivery failed')
            
            if reminder.should_retry():
                self.retry(countdown=300)
        
        reminder.save()
    
    except Reminder.DoesNotExist:
        logger.error(f"Reminder {reminder_id} not found")
    except Exception as exc:
        logger.error(f"Error sending WhatsApp reminder: {str(exc)}")
        self.retry(exc=exc, countdown=300)


@shared_task
def send_email_reminder(reminder_id):
    """Send email reminder to patient."""
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        reminder = Reminder.objects.get(id=reminder_id)
        
        if not reminder.patient.consent_email:
            reminder.status = 'failed'
            reminder.delivery_status = 'Patient declined email'
            reminder.save()
            return
        
        recipient_email = reminder.patient.user.email
        
        send_mail(
            subject=f"Medication Reminder: {reminder.prescription.drug_name}",
            message=reminder.message_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        
        reminder.mark_as_sent()
        reminder.delivery_status = 'Email Sent Successfully'
        reminder.save()
        logger.info(f"Email reminder sent to {recipient_email}")
    
    except Reminder.DoesNotExist:
        logger.error(f"Reminder {reminder_id} not found")
    except Exception as exc:
        logger.error(f"Error sending email reminder: {str(exc)}")


@shared_task
def send_scheduled_reminders():
    """
    Main task: Check for pending reminders and send them.
    Runs every minute (configurable in CELERY_BEAT_SCHEDULE).
    """
    now = timezone.now()
    
    # Get all pending reminders scheduled for now (with 5-minute grace period)
    pending_reminders = Reminder.objects.filter(
        status='pending',
        scheduled_time__lte=now + timedelta(minutes=5),
        scheduled_time__gte=now - timedelta(minutes=5)
    )
    
    logger.info(f"Found {pending_reminders.count()} reminders to send")
    
    for reminder in pending_reminders:
        # Check if patient consents to this channel
        if not reminder.can_be_sent():
            reminder.status = 'failed'
            reminder.delivery_status = 'Patient declined this channel'
            reminder.save()
            continue
        
        # Send reminder via appropriate channel
        if reminder.reminder_type == 'sms':
            send_sms_reminder.delay(reminder.id)
        elif reminder.reminder_type == 'whatsapp':
            send_whatsapp_reminder.delay(reminder.id)
        elif reminder.reminder_type == 'email':
            send_email_reminder.delay(reminder.id)


@shared_task
def check_and_alert_missed_doses():
    """
    Check for missed doses and create alerts for healthcare providers.
    Runs hourly.
    """
    now = timezone.now()
    overdue_window = now - timedelta(hours=2)  # Check doses overdue by 2+ hours
    
    # Find overdue pending doses
    overdue_doses = DoseLog.objects.filter(
        status='pending',
        scheduled_time__lte=overdue_window
    ).select_related('prescription', 'patient')
    
    logger.info(f"Found {overdue_doses.count()} overdue doses")
    
    for dose in overdue_doses:
        # Mark as missed if still pending after grace period
        dose.mark_as_missed("Automatically marked as missed after grace period")
        
        # Check if threshold for alerts is reached
        prescription = dose.prescription
        patient = dose.patient
        
        # Count recent missed doses for this prescription
        recent_missed = DoseLog.objects.filter(
            prescription=prescription,
            status='missed',
            created_at__gte=now - timedelta(days=1)
        ).count()
        
        # Check if we should escalate
        if patient.palliative_care and patient.palliative_care.is_active_plan():
            threshold = patient.palliative_care.missed_dose_alert_threshold
            
            if recent_missed >= threshold:
                # Create or update alert
                alert, created = RemissionAlert.objects.get_or_create(
                    patient=patient,
                    prescription=prescription,
                    alert_type='multiple_missed',
                    is_resolved=False,
                    defaults={
                        'alert_level': 'critical',
                        'message': f"Patient missed {recent_missed} doses of {prescription.drug_name} in the last 24 hours",
                    }
                )
                
                if created:
                    # Notify doctor and nurse
                    notify_healthcare_provider.delay(alert.id, 'doctor')
                    if patient.assigned_nurse:
                        notify_healthcare_provider.delay(alert.id, 'nurse')


@shared_task
def notify_healthcare_provider(alert_id, provider_type):
    """
    Send notification to doctor or nurse about missed doses.
    
    Args:
        alert_id: ID of the RemissionAlert
        provider_type: 'doctor' or 'nurse'
    """
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        alert = RemissionAlert.objects.get(id=alert_id)
        
        if provider_type == 'doctor':
            provider = alert.patient.assigned_doctor
            if provider:
                send_mail(
                    subject=f"ALERT: Multiple Missed Doses - {alert.patient.user.email}",
                    message=alert.message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[provider.email],
                    fail_silently=False,
                )
                alert.notified_doctor = True
        
        elif provider_type == 'nurse':
            provider = alert.patient.assigned_nurse
            if provider:
                send_mail(
                    subject=f"ALERT: Multiple Missed Doses - {alert.patient.user.email}",
                    message=alert.message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[provider.email],
                    fail_silently=False,
                )
                alert.notified_nurse = True
        
        alert.save()
        logger.info(f"Notification sent to {provider_type} for alert {alert_id}")
    
    except RemissionAlert.DoesNotExist:
        logger.error(f"Alert {alert_id} not found")
    except Exception as exc:
        logger.error(f"Error notifying {provider_type}: {str(exc)}")


@shared_task
def generate_daily_adherence_summary():
    """
    Generate daily adherence summary showing medication compliance rates.
    Useful for doctors' dashboards.
    """
    from django.db.models import Count, Q
    from datetime import date
    
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    patients = Patient.objects.filter(is_active=True)
    
    summary_data = []
    
    for patient in patients:
        doses_yesterday = DoseLog.objects.filter(
            patient=patient,
            created_at__date=yesterday
        )
        
        if doses_yesterday.exists():
            taken = doses_yesterday.filter(status='taken').count()
            total = doses_yesterday.count()
            adherence_rate = (taken / total * 100) if total > 0 else 0
            
            summary_data.append({
                'patient_id': patient.id,
                'patient_email': patient.user.email,
                'adherence_rate': adherence_rate,
                'doses_taken': taken,
                'total_doses': total,
                'date': yesterday,
            })
    
    logger.info(f"Generated adherence summary for {len(summary_data)} patients")
    return summary_data


@shared_task
def cleanup_old_reminders():
    """
    Clean up old reminder records (older than 90 days).
    Runs daily.
    """
    cutoff_date = timezone.now() - timedelta(days=90)
    
    deleted_count, _ = Reminder.objects.filter(
        created_at__lt=cutoff_date,
        status__in=['sent', 'failed', 'delivery_failed']
    ).delete()
    
    logger.info(f"Deleted {deleted_count} old reminder records")


@shared_task
def check_prescription_expiry():
    """
    Check for expiring prescriptions and notify doctors.
    Runs daily.
    """
    from django.core.mail import send_mail
    from django.conf import settings
    
    today = timezone.now().date()
    expiry_warning_date = today + timedelta(days=3)  # Warn 3 days before expiry
    
    expiring_prescriptions = Prescription.objects.filter(
        end_date=expiry_warning_date,
        is_active=True
    )
    
    for prescription in expiring_prescriptions:
        if prescription.doctor:
            send_mail(
                subject=f"Prescription Expiring Soon: {prescription.drug_name}",
                message=f"Your prescription for {prescription.patient.user.email} is expiring on {prescription.end_date}.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[prescription.doctor.email],
                fail_silently=True,
            )
    
    logger.info(f"Sent expiry warnings for {expiring_prescriptions.count()} prescriptions")
