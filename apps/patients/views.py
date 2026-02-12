"""
API Views for Patients app - Patient profile and management.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from apps.patients.models import Patient, PatientContactLog
from apps.patients.serializers import (
    PatientSerializer, PatientDetailSerializer, PatientCreateUpdateSerializer,
    PatientContactLogSerializer, PatientListSerializer
)
from apps.users.permissions import (
    IsDoctor, IsPatient, IsOwnPatientProfile, CanAccessPatientData, IsAdmin
)


class PatientViewSet(viewsets.ModelViewSet):
    """
    Patient management viewset.
    
    Endpoints:
    - GET /api/patients/ - List patients (filtered by role)
    - POST /api/patients/ - Create new patient (admin/doctor)
    - GET /api/patients/{id}/ - Get patient details
    - PATCH /api/patients/{id}/ - Update patient profile
    - GET /api/patients/{id}/prescriptions/ - Get patient's prescriptions
    - GET /api/patients/{id}/adherence-report/ - Get adherence data
    - POST /api/patients/{id}/contact-log/ - Log patient contact
    """
    
    queryset = Patient.objects.select_related('user', 'assigned_doctor', 'assigned_nurse')
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['care_category', 'is_active', 'assigned_doctor']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    ordering_fields = ['created_at', 'user__email', 'care_category']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PatientDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PatientCreateUpdateSerializer
        elif self.action == 'list':
            return PatientListSerializer
        return PatientSerializer
    
    def get_permissions(self):
        if self.action in ['create']:
            return [IsAdmin() or IsDoctor()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return super().get_permissions()
    
    def get_queryset(self):
        """Filter patients based on user role."""
        user = self.request.user
        
        if user.is_admin():
            return Patient.objects.all()
        elif user.is_doctor():
            # Doctors see only their assigned patients
            return Patient.objects.filter(assigned_doctor=user)
        elif user.is_nurse():
            # Nurses see their assigned patients
            return Patient.objects.filter(assigned_nurse=user)
        elif user.is_patient():
            # Patients see only themselves
            return Patient.objects.filter(user=user)
        
        return Patient.objects.none()
    
    def perform_create(self, serializer):
        """Create patient and associated user."""
        # This should be handled in the serializer
        serializer.save()
    
    @action(detail=True, methods=['get'])
    def prescriptions(self, request, pk=None):
        """Get all prescriptions for a patient."""
        patient = self.get_object()
        prescriptions = patient.prescriptions.all()
        
        from apps.prescriptions.serializers import PrescriptionSerializer
        serializer = PrescriptionSerializer(prescriptions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def adherence_report(self, request, pk=None):
        """Get medication adherence report for a patient."""
        patient = self.get_object()
        
        # Get adherence data for different time periods
        adherence_30 = patient.get_adherence_rate(days=30)
        adherence_7 = patient.get_adherence_rate(days=7)
        
        from apps.prescriptions.models import DoseLog
        from django.utils import timezone
        from datetime import timedelta
        
        # Get missed doses
        missed_doses = DoseLog.objects.filter(
            patient=patient,
            status='missed',
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        return Response({
            'patient_id': patient.id,
            'patient_email': patient.user.email,
            'adherence_30_days': round(adherence_30, 2),
            'adherence_7_days': round(adherence_7, 2),
            'missed_doses_30_days': missed_doses,
            'care_category': patient.care_category,
            'active_prescriptions': patient.get_active_prescriptions().count(),
        })
    
    @action(detail=True, methods=['post'])
    def contact_log(self, request, pk=None):
        """Log contact with patient."""
        patient = self.get_object()
        
        serializer = PatientContactLogSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        contact_log = serializer.save(
            patient=patient,
            contacted_by=request.user
        )
        
        return Response(
            PatientContactLogSerializer(contact_log).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def contact_history(self, request, pk=None):
        """Get contact history for a patient."""
        patient = self.get_object()
        contact_logs = patient.contact_logs.all().order_by('-timestamp')[:20]
        serializer = PatientContactLogSerializer(contact_logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """Get current user's patient profile (if patient role)."""
        try:
            patient = request.user.patient_profile
            serializer = PatientDetailSerializer(patient)
            return Response(serializer.data)
        except Patient.DoesNotExist:
            return Response(
                {'error': 'Patient profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['patch'])
    def update_my_profile(self, request):
        """Update current user's patient profile."""
        try:
            patient = request.user.patient_profile
            serializer = PatientCreateUpdateSerializer(
                patient,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(PatientDetailSerializer(patient).data)
        except Patient.DoesNotExist:
            return Response(
                {'error': 'Patient profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
