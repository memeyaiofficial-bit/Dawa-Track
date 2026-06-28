"""
Celery tasks for analytics and reporting.
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task
def generate_daily_adherence_summary():
    """
    Generate daily adherence summary.
    Runs daily via celery beat schedule.
    """
    from django.db.models import Count, Q
    from datetime import date
    from apps.patients.models import Patient
    from apps.prescriptions.models import DoseLog

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
