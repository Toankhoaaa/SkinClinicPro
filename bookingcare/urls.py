from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="BookingCare API",
        default_version='v1',
        description="API documentation for BookingCare clinic scheduling",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/auth/', include('accounts.urls')),            # /api/auth/login/, /api/auth/register/
    path('api/', include('availability.urls')),       # /api/schedules/
    path('api/', include('appointments.urls')),       # /api/appointments/
    path('api/', include('patients.urls')),           # /api/patients/me/
    path('api/', include('doctor.urls')),             # /api/doctors/, /api/doctors/my-profile/
    path('api/', include('specialities.urls')),       # /api/specialities/
    path('api/', include('rooms.urls')),              # /api/rooms/
    path('api/', include('records.urls')),            # /api/appointment-records/
    path('api/', include('treatments.urls')),         # /api/treatments/
    path('api/', include('notifications.urls')),      # /api/notifications/
    
    # Thêm các app khác sau...
    # path('api/', include('specialities.urls')),
    # path('api/', include('records.urls')),
    # Swagger & Redoc
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)