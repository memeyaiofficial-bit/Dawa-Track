"""
Custom permissions for role-based access control (RBAC).
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(BasePermission):
    """Allow access only to admin users."""
    message = "Only admins are allowed to perform this action."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin()


class IsDoctor(BasePermission):
    """Allow access only to doctors."""
    message = "Only doctors are allowed to perform this action."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_doctor()


class IsNurse(BasePermission):
    """Allow access only to nurses."""
    message = "Only nurses are allowed to perform this action."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_nurse()


class IsPatient(BasePermission):
    """Allow access only to patients."""
    message = "Only patients are allowed to perform this action."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_patient()


class IsAdminOrReadOnly(BasePermission):
    """Admin can perform any action, others can only view."""
    message = "Only admins can modify this resource."
    
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated and request.user.is_admin()


class IsDoctorOrReadOnly(BasePermission):
    """Doctor can perform any action, others can only view."""
    message = "Only doctors can modify this resource."
    
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated and request.user.is_doctor()


class IsOwnPatientProfile(BasePermission):
    """Patients can only access their own profile."""
    message = "You can only access your own patient profile."
    
    def has_object_permission(self, request, view, obj):
        # Allow doctors to view their assigned patients
        if request.user.is_doctor():
            return obj.assigned_doctor == request.user
        # Patients can only view their own profile
        return obj.user == request.user


class CanViewPrescription(BasePermission):
    """
    Doctors can view all prescriptions.
    Patients can only view their own prescriptions.
    Nurses can view prescriptions for assigned patients.
    """
    message = "You don't have permission to view this prescription."
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_doctor():
            return True
        if request.user.is_nurse():
            # Nurse can view if assigned to patient
            return obj.patient.assigned_nurse == request.user
        if request.user.is_patient():
            # Patient can view own prescriptions
            return obj.patient.user == request.user
        return False


class CanEditPrescription(BasePermission):
    """Only the prescribing doctor can edit/delete prescriptions."""
    message = "Only the prescribing doctor can modify this prescription."
    
    def has_object_permission(self, request, view, obj):
        return request.user == obj.doctor


class CanAccessPatientData(BasePermission):
    """
    Control access to patient data:
    - Doctor: Can access assigned patients
    - Nurse: Can access assigned patients
    - Patient: Can access own data
    - Admin: Can access all data
    """
    message = "You don't have permission to access this patient's data."
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin():
            return True
        if request.user.is_doctor():
            return obj.assigned_doctor == request.user
        if request.user.is_nurse():
            return obj.assigned_nurse == request.user
        if request.user.is_patient():
            return obj.user == request.user
        return False


class IsStaffOrOwner(BasePermission):
    """
    Allow staff (doctor, admin, nurse) or the user owner to access.
    """
    message = "You don't have permission to perform this action."
    
    def has_object_permission(self, request, view, obj):
        # Allow staff members
        if request.user.is_admin() or request.user.is_doctor() or request.user.is_nurse():
            return True
        # Allow the user accessing their own data
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False
