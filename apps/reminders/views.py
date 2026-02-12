"""
API Views for Reminders app - Medication reminders and alerts.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from datetime import timedelta
from apps.reminders.models import (
    Reminder, ReminderTemplate, ReminderResponse, RemissionAlert
)
from apps.reminders.serializers import (
    ReminderSerializer, ReminderDetailSerializer, ReminderTemplateSerializer,
    ReminderResponseSerializer, ReminderResponseCreateSerializer,
    RemissionAlertSerializer, RemissionAlertDetailSerializer,
    BulkReminderCreateSerializer
)
from apps.users.permissions import IsDoctor, IsPatient, IsAdmin


class ReminderViewSet(viewsets.ModelViewSet):
    """
    Reminder management viewset.
    
    Endpoints:
    - GET /api/reminders/ - List reminders (filtered by role)
    - POST /api/reminders/ - Create reminder (doctor only)
    - GET /api/reminders/{id}/ - Get reminder details
    - POST /api/reminders/bulk-create/ - Create multiple reminders
    - GET /api/reminders/pending/ - List pending reminders
    - GET /api/reminders/my-pending/ - Get patient's pending reminders
    """
    
    queryset = Reminder.objects.select_related('prescription', 'patient')
    serializer_class = ReminderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['patient', 'status', 'reminder_type']
    ordering_fields = ['scheduled_time', 'created_at']
    ordering = ['-scheduled_time']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ReminderDetailSerializer
        elif self.action == 'bulk_create':
            return BulkReminderCreateSerializer
        return ReminderSerializer
    
    def get_queryset(self):
        """Filter reminders based on user role."""
        user = self.request.user
        
        if user.is_admin():
            return Reminder.objects.all()
        elif user.is_doctor():
            return Reminder.objects.filter(prescription__doctor=user)
        elif user.is_nurse():
            return Reminder.objects.filter(patient__assigned_nurse=user)
        elif user.is_patient():
            return Reminder.objects.filter(patient__user=user)
        
        return Reminder.objects.none()
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get all pending reminders (admin/staff only)."""
        if not (request.user.is_admin() or request.user.is_doctor() or request.user.is_nurse()):
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        pending = self.get_queryset().filter(status='pending').order_by('scheduled_time')
        serializer = ReminderDetailSerializer(pending, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_pending(self, request):
        """Get patient's pending reminders."""
        if not request.user.is_patient():
            return Response(
                {'error': 'Only patients can view their pending reminders'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from apps.patients.models import Patient
        try:
            patient = Patient.objects.get(user=request.user)
            pending = Reminder.objects.filter(
                patient=patient,
                status='pending',
                scheduled_time__gte=timezone.now() - timedelta(hours=1)
            ).order_by('scheduled_time')
            
            serializer = ReminderDetailSerializer(pending, many=True)
            return Response(serializer.data)
        except Patient.DoesNotExist:
            return Response(
                {'error': 'Patient profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Patient responds to a reminder."""
        reminder = self.get_object()
        
        # Verify patient ownership
        from apps.patients.models import Patient
        try:
            patient = Patient.objects.get(user=request.user)
            if reminder.patient != patient:
                return Response(
                    {'error': 'This is not your reminder'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Patient.DoesNotExist:
            return Response(
                {'error': 'Patient profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ReminderResponseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create response and update dose log
        response = serializer.save(reminder=reminder)
        
        # If confirmed as taken, mark dose log
        if response.response_type == 'acknowledged':
            from apps.prescriptions.models import DoseLog
            try:
                dose_log = DoseLog.objects.get(
                    prescription=reminder.prescription,
                    patient=reminder.patient,
                    scheduled_time=reminder.scheduled_time
                )
                dose_log.mark_as_taken()
            except DoseLog.DoesNotExist:
                pass
        
        return Response(
            ReminderResponseSerializer(response).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create reminders for multiple prescriptions."""
        if not (request.user.is_admin() or request.user.is_doctor()):
            return Response(
                {'error': 'Only doctors and admins can create reminders'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        from apps.prescriptions.models import Prescription
        from apps.reminders.tasks import send_scheduled_reminders
        
        prescription_ids = serializer.validated_data['prescription_ids']
        reminder_type = serializer.validated_data['reminder_type']
        
        created_count = 0
        errors = []
        
        for rx_id in prescription_ids:
            try:
                prescription = Prescription.objects.get(id=rx_id)
                
                # Create reminders based on schedule
                schedules = prescription.schedule_times.all()
                current_date = timezone.now().date()
                
                while current_date <= prescription.end_date:
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
            
            except Prescription.DoesNotExist:
                errors.append(f"Prescription {rx_id} not found")
        
        return Response({
            'message': f'Created {created_count} reminders',
            'created_count': created_count,
            'errors': errors,
        })


class RemissionAlertViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Missed dose alert viewset.
    
    Endpoints:
    - GET /api/alerts/ - List alerts (filtered by role)
    - GET /api/alerts/{id}/ - Get alert details
    - GET /api/alerts/unresolved/ - Get unresolved alerts
    """
    
    queryset = RemissionAlert.objects.select_related('patient', 'prescription')
    serializer_class = RemissionAlertSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['patient', 'is_resolved', 'alert_level']
    ordering_fields = ['created_at', 'alert_level']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RemissionAlertDetailSerializer
        return RemissionAlertSerializer
    
    def get_queryset(self):
        """Filter alerts based on user role."""
        user = self.request.user
        
        if user.is_admin():
            return RemissionAlert.objects.all()
        elif user.is_doctor():
            return RemissionAlert.objects.filter(patient__assigned_doctor=user)
        elif user.is_nurse():
            return RemissionAlert.objects.filter(patient__assigned_nurse=user)
        
        return RemissionAlert.objects.none()
    
    @action(detail=False, methods=['get'])
    def unresolved(self, request):
        """Get unresolved alerts."""
        unresolved = self.get_queryset().filter(is_resolved=False)
        serializer = RemissionAlertDetailSerializer(unresolved, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark alert as resolved."""
        alert = self.get_object()
        alert.resolve()
        return Response({
            'message': 'Alert resolved',
            'resolved_at': alert.resolved_at,
        })


class ReminderTemplateViewSet(viewsets.ModelViewSet):
    """
    Reminder template management (admin only).
    """
    
    queryset = ReminderTemplate.objects.all()
    serializer_class = ReminderTemplateSerializer
    permission_classes = [IsAdmin()]
