"""
Serializers for Prescriptions app.
"""
from rest_framework import serializers
from django.utils import timezone
from apps.prescriptions.models import (
    Prescription, PrescriptionSchedule, DoseLog, PrescriptionChange
)


class PrescriptionScheduleSerializer(serializers.ModelSerializer):
    """Prescription schedule times."""
    
    class Meta:
        model = PrescriptionSchedule
        fields = ['id', 'scheduled_time', 'description', 'day_index']
        read_only_fields = ['id']


class PrescriptionSerializer(serializers.ModelSerializer):
    """Basic prescription information."""
    
    doctor_email = serializers.CharField(source='doctor.email', read_only=True)
    patient_email = serializers.CharField(source='patient.user.email', read_only=True)
    schedule_times = PrescriptionScheduleSerializer(many=True, read_only=True)
    days_remaining = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = Prescription
        fields = ['id', 'patient_email', 'doctor_email', 'drug_name',
                  'dosage', 'frequency', 'duration_days', 'start_date',
                  'end_date', 'is_comfort_medication', 'is_active',
                  'schedule_times', 'days_remaining', 'is_expired',
                  'created_at']
        read_only_fields = ['id', 'created_at', 'end_date']
    
    def get_days_remaining(self, obj):
        if obj.is_expired():
            return 0
        return (obj.end_date - timezone.now().date()).days
    
    def get_is_expired(self, obj):
        return obj.is_expired()


class PrescriptionDetailSerializer(serializers.ModelSerializer):
    """Detailed prescription information."""
    
    doctor_info = serializers.SerializerMethodField()
    patient_info = serializers.SerializerMethodField()
    schedule_times = PrescriptionScheduleSerializer(many=True, read_only=True)
    days_remaining = serializers.SerializerMethodField()
    total_doses = serializers.SerializerMethodField()
    adherence_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Prescription
        fields = ['id', 'patient_info', 'doctor_info', 'drug_name', 'drug_code',
                  'dosage', 'frequency', 'custom_frequency_description',
                  'duration_days', 'start_date', 'end_date', 'indication',
                  'notes', 'is_comfort_medication', 'is_active',
                  'schedule_times', 'days_remaining', 'total_doses',
                  'adherence_percentage', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'end_date']
    
    def get_doctor_info(self, obj):
        if obj.doctor:
            return {
                'id': obj.doctor.id,
                'email': obj.doctor.email,
                'name': f"{obj.doctor.first_name} {obj.doctor.last_name}"
            }
        return None
    
    def get_patient_info(self, obj):
        return {
            'id': obj.patient.id,
            'email': obj.patient.user.email,
            'name': f"{obj.patient.user.first_name} {obj.patient.user.last_name}"
        }
    
    def get_days_remaining(self, obj):
        if obj.is_expired():
            return 0
        return (obj.end_date - timezone.now().date()).days
    
    def get_total_doses(self, obj):
        return obj.get_total_doses()
    
    def get_adherence_percentage(self, obj):
        logs = obj.dose_logs.all()
        if not logs.exists():
            return None
        taken = logs.filter(status='taken').count()
        return round((taken / logs.count()) * 100, 2) if logs.count() > 0 else 0


class PrescriptionCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating prescriptions."""
    
    schedule_times = PrescriptionScheduleSerializer(many=True, required=False)
    
    class Meta:
        model = Prescription
        fields = ['patient', 'drug_name', 'drug_code', 'dosage', 'frequency',
                  'custom_frequency_description', 'duration_days', 'start_date',
                  'indication', 'notes', 'is_comfort_medication', 'schedule_times']
    
    def validate_frequency(self, value):
        if value == 'custom' and not self.initial_data.get('schedule_times'):
            raise serializers.ValidationError(
                "Custom frequency requires schedule_times."
            )
        return value
    
    def create(self, validated_data):
        schedule_times_data = validated_data.pop('schedule_times', [])
        prescription = Prescription.objects.create(**validated_data)
        
        for schedule_data in schedule_times_data:
            PrescriptionSchedule.objects.create(
                prescription=prescription,
                **schedule_data
            )
        
        return prescription
    
    def update(self, instance, validated_data):
        schedule_times_data = validated_data.pop('schedule_times', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if schedule_times_data is not None:
            instance.schedule_times.all().delete()
            for schedule_data in schedule_times_data:
                PrescriptionSchedule.objects.create(
                    prescription=instance,
                    **schedule_data
                )
        
        return instance


class DoseLogSerializer(serializers.ModelSerializer):
    """Serializer for dose logs."""
    
    drug_name = serializers.CharField(source='prescription.drug_name', read_only=True)
    patient_name = serializers.CharField(source='patient.user.email', read_only=True)
    confirmed_by_name = serializers.CharField(source='confirmed_by.email', read_only=True, allow_null=True)
    
    class Meta:
        model = DoseLog
        fields = ['id', 'drug_name', 'patient_name', 'scheduled_time',
                  'actual_intake_time', 'status', 'notes', 'confirmed_by_name',
                  'confirmation_method', 'created_at']
        read_only_fields = ['id', 'created_at']


class DoseLogUpdateSerializer(serializers.ModelSerializer):
    """Serializer for patients to confirm dose taken."""
    
    class Meta:
        model = DoseLog
        fields = ['status', 'notes']
    
    def validate_status(self, value):
        allowed_statuses = ['taken', 'missed', 'skipped']
        if value not in allowed_statuses:
            raise serializers.ValidationError(
                f"Status must be one of: {', '.join(allowed_statuses)}"
            )
        return value


class PrescriptionChangeSerializer(serializers.ModelSerializer):
    """Serializer for prescription change history."""
    
    changed_by_name = serializers.CharField(source='changed_by.email', read_only=True)
    
    class Meta:
        model = PrescriptionChange
        fields = ['id', 'action', 'changed_by_name', 'old_values', 'new_values',
                  'reason', 'timestamp']
        read_only_fields = fields
