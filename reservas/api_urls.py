from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, LocationViewSet, ReservationViewSet,
    LocationImageUploadView, OwnerDashboardView, CustomerReservationsView,
    UserTypeView, PaymentCreateView
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'locations', LocationViewSet)
router.register(r'reservations', ReservationViewSet)

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='api-register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/user-type/', UserTypeView.as_view(), name='user-type'),
    path('owner/dashboard/', OwnerDashboardView.as_view(), name='api-owner-dashboard'),
    path('customer/reservations/', CustomerReservationsView.as_view(), name='customer-reservations'),
    path('payments/', PaymentCreateView.as_view(), name='payment-create'),
    path('locations/images/upload/', LocationImageUploadView.as_view(), name='location-image-upload'),
]

urlpatterns += router.urls