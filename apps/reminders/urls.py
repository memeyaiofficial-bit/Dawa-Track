"""
URL routing for Reminders app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.reminders.views import (
    ReminderViewSet, RemissionAlertViewSet, ReminderTemplateViewSet
)

router = DefaultRouter()
router.register(r'reminders', ReminderViewSet, basename='reminder')
router.register(r'alerts', RemissionAlertViewSet, basename='alert')
router.register(r'templates', ReminderTemplateViewSet, basename='template')

urlpatterns = [
    path('', include(router.urls)),
]
