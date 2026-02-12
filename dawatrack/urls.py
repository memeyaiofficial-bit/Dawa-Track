from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # JWT Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # App URLs
    path('api/users/', include('apps.users.urls')),
    path('api/patients/', include('apps.patients.urls')),
    path('api/prescriptions/', include('apps.prescriptions.urls')),
    path('api/reminders/', include('apps.reminders.urls')),
    path('api/palliative-care/', include('apps.palliative_care.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    
    # Dashboard pages (non-API)
    path('dashboard/doctor/', include('apps.dashboards.urls')),
    path('dashboard/admin/', include('apps.dashboards.urls')),
    path('dashboard/patient/', include('apps.dashboards.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
