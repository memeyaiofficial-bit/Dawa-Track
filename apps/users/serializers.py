"""
Serializers for User app - Convert Django models to JSON.
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from apps.users.models import User, UserPermission, AuditLog


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer."""
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 
                  'phone_number', 'role', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError("Email already in use.")
        return value


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed user serializer with permissions."""
    
    custom_permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 
                  'phone_number', 'role', 'profile_completed', 'is_active', 
                  'last_login', 'date_joined', 'custom_permissions']
        read_only_fields = ['id', 'last_login', 'date_joined']
    
    def get_custom_permissions(self, obj):
        try:
            perms = obj.custom_permissions
            return perms.permissions
        except UserPermission.DoesNotExist:
            return []


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(write_only=True, min_length=12)
    password_confirm = serializers.CharField(write_only=True, min_length=12)
    
    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 
                  'phone_number', 'password', 'password_confirm', 'role']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError(
                {"password": "Passwords do not match."}
            )
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        # Create default permission object
        UserPermission.objects.create(user=user)
        return user


class DoctorSerializer(serializers.ModelSerializer):
    """Detailed doctor information."""
    
    user_info = UserSerializer(source='user', read_only=True)
    patient_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'user_info', 'email', 'specialty', 'patient_count']
    
    def get_patient_count(self, obj):
        return obj.patients_as_doctor.filter(is_active=True).count()


class passwordChangeSerializer(serializers.Serializer):
    """Serializer for password changes."""
    
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=12)
    new_password_confirm = serializers.CharField(write_only=True, min_length=12)
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
    
    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError(
                {"new_password": "Passwords do not match."}
            )
        return data
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for audit logs (read-only)."""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = ['id', 'user_email', 'action', 'ip_address', 'timestamp', 
                  'success', 'details']
        read_only_fields = fields
