from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.owner_dashboard, name='dashboard'),
    path('locations/create/', views.create_location, name='location-create'),
    path('reservations/create/', views.create_reservation, name='reservation-create'),
    path('reservations/list/', views.list_reservations, name='reservation-list'),
]