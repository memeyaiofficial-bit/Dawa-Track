"""
Serializers for Reminders app.
"""
from rest_framework import serializers
from apps.reminders.models import (
    Reminder, ReminderTemplate, ReminderResponse, RemissionAlert
)


class ReminderSerializer(serializers.ModelSerializer):
    """Basic reminder information."""
    
    patient_email = serializers.CharField(source='patient.user.email', read_only=True)
    drug_name = serializers.CharField(source='prescription.drug_name', read_only=True)
    
    class Meta:
        model = Reminder
        fields = ['id', 'patient_email', 'drug_name', 'scheduled_time',
                  'reminder_type', 'status', 'sent_at', 'created_at']
        read_only_fields = ['id', 'created_at', 'sent_at']


class ReminderDetailSerializer(serializers.ModelSerializer):
    """Detailed reminder information."""
    
    patient_name = serializers.SerializerMethodField()
    drug_info = serializers.SerializerMethodField()
    response = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    can_be_sent = serializers.SerializerMethodField()
    
    class Meta:
        model = Reminder
        fields = ['id', 'patient_name', 'drug_info', 'scheduled_time',
                  'reminder_type', 'message_content', 'status', 'sent_at',
                  'delivery_status', 'external_message_id', 'retry_count',
                  'response', 'is_overdue', 'can_be_sent', 'created_at']
        read_only_fields = ['id', 'created_at', 'sent_at', 'external_message_id']
    
    def get_patient_name(self, obj):
        return f"{obj.patient.user.first_name} {obj.patient.user.last_name}"
    
    def get_drug_info(self, obj):
        return {
            'name': obj.prescription.drug_name,
            'dosage': obj.prescription.dosage,
            'frequency': obj.prescription.get_frequency_display(),
        }
    
    def get_response(self, obj):
        if hasattr(obj, 'response'):
            return {
                'type': obj.response.response_type,
                'message': obj.response.message,
                'received_at': obj.response.received_at,
            }
        return None
    
    def get_is_overdue(self, obj):
        return obj.is_overdue()
    
    def get_can_be_sent(self, obj):
        return obj.can_be_sent()


class ReminderTemplateSerializer(serializers.ModelSerializer):
    """Reminder template serializer."""
    
    class Meta:
        model = ReminderTemplate
        fields = ['id', 'name', 'reminder_type', 'message_template', 'is_active']
        read_only_fields = ['id']


class ReminderResponseSerializer(serializers.ModelSerializer):
    """Patient response to reminder."""
    
    reminder_info = serializers.SerializerMethodField()
    
    class Meta:
        model = ReminderResponse
        fields = ['id', 'reminder_info', 'response_type', 'message', 'received_at']
        read_only_fields = ['id', 'received_at']
    
    def get_reminder_info(self, obj):
        return {
            'id': obj.reminder.id,
            'drug': obj.reminder.prescription.drug_name,
            'scheduled_time': obj.reminder.scheduled_time,
        }


class ReminderResponseCreateSerializer(serializers.ModelSerializer):
    """Serializer for patients to respond to reminders."""
    
    class Meta:
        model = ReminderResponse
        fields = ['response_type', 'message']


class RemissionAlertSerializer(serializers.ModelSerializer):
    """Alert for missed doses and low adherence."""
    
    patient_name = serializers.CharField(source='patient.user.email', read_only=True)
    drug_name = serializers.CharField(source='prescription.drug_name', read_only=True, allow_null=True)
    
    class Meta:
        model = RemissionAlert
        fields = ['id', 'patient_name', 'drug_name', 'alert_type', 'alert_level',
                  'message', 'notified_doctor', 'notified_nurse', 'is_resolved',
                  'created_at', 'resolved_at']
        read_only_fields = ['id', 'created_at', 'resolved_at']


class RemissionAlertDetailSerializer(serializers.ModelSerializer):
    """Detailed alert information for healthcare providers."""
    
    patient_info = serializers.SerializerMethodField()
    prescription_info = serializers.SerializerMethodField()
    
    class Meta:
        model = RemissionAlert
        fields = ['id', 'patient_info', 'prescription_info', 'alert_type',
                  'alert_level', 'message', 'notified_doctor', 'notified_nurse',
                  'is_resolved', 'created_at', 'resolved_at']
        read_only_fields = fields
    
    def get_patient_info(self, obj):
        return {
            'id': obj.patient.id,
            'email': obj.patient.user.email,
            'name': f"{obj.patient.user.first_name} {obj.patient.user.last_name}",
            'phone': obj.patient.user.phone_number,
        }
    
    def get_prescription_info(self, obj):
        if obj.prescription:
            return {
                'id': obj.prescription.id,
                'drug': obj.prescription.drug_name,
                'dosage': obj.prescription.dosage,
                'frequency': obj.prescription.get_frequency_display(),
            }
        return None


class BulkReminderCreateSerializer(serializers.Serializer):
    """Serializer for bulk reminder creation."""
    
    prescription_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of prescription IDs to create reminders for"
    )
    reminder_type = serializers.ChoiceField(
        choices=['sms', 'whatsapp', 'email', 'push']
    )
    schedule_date = serializers.DateField(required=False)
    
    def validate_prescription_ids(self, value):
        from apps.prescriptions.models import Prescription
        if not value:
            raise serializers.ValidationError("At least one prescription ID required.")
        return value
