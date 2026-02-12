"""
Serializers for Patients app.
"""
from rest_framework import serializers
from apps.patients.models import Patient, PatientContactLog
from apps.users.serializers import UserSerializer


class PatientSerializer(serializers.ModelSerializer):
    """Basic patient information serializer."""
    
    user_info = UserSerializer(source='user', read_only=True)
    age = serializers.SerializerMethodField()
    adherence_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = Patient
        fields = ['id', 'user_info', 'date_of_birth', 'age', 'gender', 
                  'blood_type', 'care_category', 'emergency_contact_name',
                  'emergency_contact_phone', 'preferred_reminder_channel',
                  'is_active', 'created_at', 'adherence_rate']
        read_only_fields = ['id', 'created_at', 'adherence_rate']
    
    def get_age(self, obj):
        return obj.age
    
    def get_adherence_rate(self, obj):
        return round(obj.get_adherence_rate(days=30), 2)


class PatientDetailSerializer(serializers.ModelSerializer):
    """Detailed patient information for doctors."""
    
    user_info = UserSerializer(source='user', read_only=True)
    doctor_info = UserSerializer(source='assigned_doctor', read_only=True)
    nurse_info = UserSerializer(source='assigned_nurse', read_only=True)
    age = serializers.SerializerMethodField()
    adherence_rate = serializers.SerializerMethodField()
    active_prescriptions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Patient
        fields = ['id', 'user_info', 'date_of_birth', 'age', 'gender',
                  'blood_type', 'care_category', 'medical_history',
                  'current_conditions', 'allergies', 'emergency_contact_name',
                  'emergency_contact_phone', 'emergency_contact_relationship',
                  'doctor_info', 'nurse_info', 'preferred_reminder_channel',
                  'reminder_time_preference', 'consent_sms', 'consent_whatsapp',
                  'consent_email', 'is_active', 'created_at', 'updated_at',
                  'adherence_rate', 'active_prescriptions_count']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_age(self, obj):
        return obj.age
    
    def get_adherence_rate(self, obj):
        return round(obj.get_adherence_rate(days=30), 2)
    
    def get_active_prescriptions_count(self, obj):
        return obj.get_active_prescriptions().count()


class PatientCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating patient profiles."""
    
    class Meta:
        model = Patient
        fields = ['date_of_birth', 'gender', 'blood_type', 'care_category',
                  'emergency_contact_name', 'emergency_contact_phone',
                  'emergency_contact_relationship', 'medical_history',
                  'current_conditions', 'allergies', 'assigned_doctor',
                  'assigned_nurse', 'preferred_reminder_channel',
                  'reminder_time_preference', 'consent_sms', 'consent_whatsapp',
                  'consent_email']
    
    def validate_assigned_doctor(self, value):
        if value and not value.is_doctor():
            raise serializers.ValidationError("Assigned user must be a doctor.")
        return value
    
    def validate_assigned_nurse(self, value):
        if value and not value.is_nurse():
            raise serializers.ValidationError("Assigned user must be a nurse.")
        return value


class PatientContactLogSerializer(serializers.ModelSerializer):
    """Serializer for patient contact logs."""
    
    contacted_by_name = serializers.CharField(source='contacted_by.email', read_only=True)
    
    class Meta:
        model = PatientContactLog
        fields = ['id', 'contact_type', 'contacted_by_name', 'notes', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class PatientListSerializer(serializers.ModelSerializer):
    """Light serializer for patient lists."""
    
    email = serializers.CharField(source='user.email')
    name = serializers.SerializerMethodField()
    adherence_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = Patient
        fields = ['id', 'email', 'name', 'care_category', 'adherence_rate', 'is_active']
    
    def get_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email
    
    def get_adherence_rate(self, obj):
        return round(obj.get_adherence_rate(days=30), 2)
