"""
API Views for Users app - Authentication and user management.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate
from apps.users.models import User, AuditLog
from apps.users.serializers import (
    UserSerializer, UserDetailSerializer, UserRegistrationSerializer,
    passwordChangeSerializer, AuditLogSerializer
)
from apps.users.permissions import IsAdmin


class UserViewSet(viewsets.ModelViewSet):
    """
    User management viewset.
    
    Endpoints:
    - POST /api/users/register/ - Register new user
    - POST /api/users/login/ - Login (returns JWT token)
    - GET /api/users/me/ - Get current user profile
    - PATCH /api/users/me/ - Update current user profile
    - POST /api/users/change-password/ - Change password
    - GET /api/users/ - List all users (admin only)
    """
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'register':
            return UserRegistrationSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        elif self.action == 'change_password':
            return passwordChangeSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action == 'register':
            return [AllowAny()]
        elif self.action == 'list':
            return [IsAdmin()]
        return super().get_permissions()
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """Register a new user account."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Log registration
        AuditLog.objects.create(
            user=user,
            action='account_created',
            ip_address=self.get_client_ip(request),
            success=True,
        )
        
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        Login endpoint - returns JWT token.
        Expects: email, password
        """
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Email and password required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            AuditLog.objects.create(
                user=None,
                action='login_failed',
                ip_address=self.get_client_ip(request),
                success=False,
                details={'reason': 'user_not_found', 'email': email}
            )
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if account is locked
        if user.is_locked:
            AuditLog.objects.create(
                user=user,
                action='login_failed',
                ip_address=self.get_client_ip(request),
                success=False,
                details={'reason': 'account_locked'}
            )
            return Response(
                {'error': 'Account is locked. Contact administrator.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Authenticate
        if not user.check_password(password):
            user.increment_failed_login()
            AuditLog.objects.create(
                user=user,
                action='login_failed',
                ip_address=self.get_client_ip(request),
                success=False,
                details={'reason': 'wrong_password'}
            )
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Successful login
        user.reset_login_attempts()
        user.last_login_ip = self.get_client_ip(request)
        user.save(update_fields=['last_login_ip', 'failed_login_attempts', 'last_login'])
        
        AuditLog.objects.create(
            user=user,
            action='login',
            ip_address=self.get_client_ip(request),
            success=True,
        )
        
        # Generate JWT tokens
        from rest_framework_simplejwt.tokens import RefreshToken
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        })
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile."""
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'])
    def update_me(self, request):
        """Update current user profile."""
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change user password."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        AuditLog.objects.create(
            user=user,
            action='password_change',
            ip_address=self.get_client_ip(request),
            success=True,
        )
        
        return Response({'message': 'Password changed successfully'})
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdmin])
    def audit_logs(self, request):
        """Get audit logs (admin only)."""
        logs = AuditLog.objects.all().order_by('-timestamp')[:100]
        serializer = AuditLogSerializer(logs, many=True)
        return Response(serializer.data)
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
