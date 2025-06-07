from django.urls import path, include
from .views import RegisterView, LocationViewSet, LocationImageUploadView, ReservationViewSet,  OwnerDashboardView, CustomerReservationsView, UserTypeView, PaymentCreateView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('owner/dashboard/', OwnerDashboardView.as_view(), name='owner-dashboard'),
    path('customer/reservations/', CustomerReservationsView.as_view(), name='customer-reservations'),
    path('auth/user-type/', UserTypeView.as_view(), name='user-type'),
    path('payments/', PaymentCreateView.as_view(), name='payment-create'),
    path('locations/images/upload/', LocationImageUploadView.as_view(), name='location-image-upload'),
]

router = DefaultRouter()
router.register(r'locations', LocationViewSet)
router.register(r'reservations', ReservationViewSet)

from django.urls import include

urlpatterns += [
    path('', include(router.urls))
]