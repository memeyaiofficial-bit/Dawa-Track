"""
URL routing for Prescriptions app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.prescriptions.views import PrescriptionViewSet, DoseLogViewSet

router = DefaultRouter()
router.register(r'', PrescriptionViewSet, basename='prescription')
router.register(r'dose-logs', DoseLogViewSet, basename='dose-log')

urlpatterns = [
    path('', include(router.urls)),
]
