from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from reservas.views import LocationViewSet, ReservationViewSet

router = DefaultRouter()
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'reservations', ReservationViewSet, basename='reservation')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('reservas.urls')),  
]