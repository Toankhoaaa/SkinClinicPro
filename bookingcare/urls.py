from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/auth/', include('accounts.urls')),            # /api/auth/login/, /api/auth/register/
    path('api/', include('availability.urls')),       # /api/schedules/
    path('api/', include('appointments.urls')),       # /api/appointments/
    path('api/', include('patients.urls')),           # /api/patients/me/
    path('api/', include('doctor.urls')),             # /api/doctors/, /api/doctors/my-profile/
    
    # Thêm các app khác sau...
    # path('api/', include('specialities.urls')),
    # path('api/', include('records.urls')),
]