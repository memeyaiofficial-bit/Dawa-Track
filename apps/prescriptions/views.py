"""
API Views for Prescriptions app - Medication management and dose tracking.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from django.db.models import Q
from apps.prescriptions.models import (
    Prescription, PrescriptionSchedule, DoseLog, PrescriptionChange
)
from apps.prescriptions.serializers import (
    PrescriptionSerializer, PrescriptionDetailSerializer,
    PrescriptionCreateUpdateSerializer, DoseLogSerializer,
    DoseLogUpdateSerializer, PrescriptionChangeSerializer
)
from apps.users.permissions import IsDoctor, IsPatient, CanEditPrescription, CanViewPrescription
from apps.patients.models import Patient


class PrescriptionViewSet(viewsets.ModelViewSet):
    """
    Prescription management viewset.
    
    Endpoints:
    - GET /api/prescriptions/ - List prescriptions
    - POST /api/prescriptions/ - Create prescription (doctor only)
    - GET /api/prescriptions/{id}/ - Get prescription details
    - PATCH /api/prescriptions/{id}/ - Update prescription (doctor only)
    - DELETE /api/prescriptions/{id}/ - Delete prescription (doctor only)
    - GET /api/prescriptions/{id}/dose-logs/ - Get dose logs for prescription
    - POST /api/prescriptions/{id}/create-reminders/ - Auto-create reminders
    - GET /api/prescriptions/{id}/history/ - Get change history
    """
    
    queryset = Prescription.objects.select_related('patient', 'doctor')
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['patient', 'is_active', 'is_comfort_medication']
    search_fields = ['drug_name', 'patient__user__email']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PrescriptionDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PrescriptionCreateUpdateSerializer
        return PrescriptionSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'create_reminders']:
            return [IsDoctor()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsDoctor()]
        return super().get_permissions()
    
    def get_queryset(self):
        """Filter prescriptions based on user role."""
        user = self.request.user
        
        if user.is_admin() or user.is_doctor():
            return Prescription.objects.all()
        elif user.is_nurse():
            return Prescription.objects.filter(patient__assigned_nurse=user)
        elif user.is_patient():
            return Prescription.objects.filter(patient__user=user)
        
        return Prescription.objects.none()
    
    def perform_create(self, serializer):
        """Create prescription and log the action."""
        prescription = serializer.save(doctor=self.request.user, created_by=self.request.user)
        
        # Log prescription creation
        PrescriptionChange.objects.create(
            prescription=prescription,
            action='created',
            changed_by=self.request.user,
            reason='New prescription created'
        )
    
    @action(detail=True, methods=['get'])
    def dose_logs(self, request, pk=None):
        """Get all dose logs for a prescription."""
        prescription = self.get_object()
        
        # Optional filtering by status
        status_filter = request.query_params.get('status')
        logs = prescription.dose_logs.all()
        
        if status_filter:
            logs = logs.filter(status=status_filter)
        
        serializer = DoseLogSerializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def create_reminders(self, request, pk=None):
        """Auto-create reminders for prescription."""
        prescription = self.get_object()
        
        from apps.reminders.models import Reminder
        from apps.reminders.tasks import send_scheduled_reminders
        from datetime import timedelta
        
        reminder_type = request.data.get('reminder_type', 'whatsapp')
        
        # Create reminders based on prescription schedule
        created_count = 0
        current_date = timezone.now().date()
        
        while current_date <= prescription.end_date:
            # Get schedule times for this prescription
            schedules = prescription.schedule_times.all()
            
            if not schedules.exists():
                # Use frequency to create times
                break
            
            for schedule in schedules:
                scheduled_datetime = timezone.make_aware(
                    timezone.datetime.combine(current_date, schedule.scheduled_time)
                )
                
                if scheduled_datetime > timezone.now():
                    reminder, created = Reminder.objects.get_or_create(
                        prescription=prescription,
                        patient=prescription.patient,
                        scheduled_time=scheduled_datetime,
                        reminder_type=reminder_type,
                        defaults={
                            'message_content': Reminder.generate_reminder_message(
                                prescription, prescription.patient
                            ),
                            'status': 'pending',
                        }
                    )
                    if created:
                        created_count += 1
            
            current_date += timedelta(days=1)
        
        return Response({
            'message': f'Created {created_count} reminders',
            'count': created_count,
        })
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get prescription change history."""
        prescription = self.get_object()
        changes = prescription.change_history.all()
        serializer = PrescriptionChangeSerializer(changes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle prescription active status."""
        prescription = self.get_object()
        
        if request.user != prescription.doctor and not request.user.is_admin():
            return Response(
                {'error': 'Only the prescribing doctor can modify this'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        old_value = prescription.is_active
        prescription.is_active = not prescription.is_active
        prescription.save()
        
        # Log the change
        action_type = 'resumed' if prescription.is_active else 'suspended'
        PrescriptionChange.objects.create(
            prescription=prescription,
            action=action_type,
            changed_by=request.user,
            old_values={'is_active': old_value},
            new_values={'is_active': prescription.is_active},
            reason=request.data.get('reason', '')
        )
        
        return Response({
            'message': f'Prescription {action_type}',
            'is_active': prescription.is_active,
        })


class DoseLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Dose log viewset - Read-only for viewing dose history.
    
    Endpoints:
    - GET /api/dose-logs/ - List dose logs (filtered by patient)
    - GET /api/dose-logs/{id}/ - Get dose log details
    """
    
    queryset = DoseLog.objects.select_related('prescription', 'patient')
    serializer_class = DoseLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['patient', 'prescription', 'status']
    ordering_fields = ['scheduled_time', 'created_at']
    ordering = ['-scheduled_time']
    
    def get_queryset(self):
        """Filter dose logs based on user role."""
        user = self.request.user
        
        if user.is_admin():
            return DoseLog.objects.all()
        elif user.is_doctor():
            return DoseLog.objects.filter(prescription__doctor=user)
        elif user.is_nurse():
            return DoseLog.objects.filter(patient__assigned_nurse=user)
        elif user.is_patient():
            return DoseLog.objects.filter(patient__user=user)
        
        return DoseLog.objects.none()
    
    @action(detail=True, methods=['patch'])
    def mark_taken(self, request, pk=None):
        """Patient confirms dose was taken."""
        dose_log = self.get_object()
        
        if dose_log.patient.user != request.user:
            return Response(
                {'error': 'You can only confirm your own doses'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        dose_log.mark_as_taken()
        return Response(DoseLogSerializer(dose_log).data)
    
    @action(detail=True, methods=['patch'])
    def mark_missed(self, request, pk=None):
        """Patient or staff marks dose as missed."""
        dose_log = self.get_object()
        
        notes = request.data.get('notes', '')
        dose_log.mark_as_missed(notes)
        
        return Response(DoseLogSerializer(dose_log).data)
