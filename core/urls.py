from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from reservas.views import LocationViewSet, ReservationViewSet
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'reservations', ReservationViewSet, basename='reservation')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('reservas.urls')),  
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)