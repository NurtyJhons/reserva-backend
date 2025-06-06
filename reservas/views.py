from rest_framework import generics, viewsets, status
from .serializers import UserRegistrationSerializer, LocationSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny, IsAuthenticated
from .models import Location, Reservation
from .permissions import IsOwnerOrReadOnly, IsReservationOwnerOrReadOnly, IsOwner
from rest_framework.response import Response
from rest_framework.decorators import action
from .serializers import ReservationSerializer, ReservationCreateSerializer
from rest_framework.views import APIView
from datetime import date
from django.db.models import Count

class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.filter(is_active=True)
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.groups.filter(name='owners').exists():
            return Location.objects.filter(owner=self.request.user)
        return Location.objects.filter(is_active=True)

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    permission_classes = [IsAuthenticated, IsReservationOwnerOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='owners').exists():
            # Owners veem reservas dos seus locais
            return Reservation.objects.filter(location__owner=user)
        else:
            # Customers veem suas reservas
            return Reservation.objects.filter(user=user)

    def get_serializer_class(self):
        if self.action == 'create':
            return ReservationCreateSerializer
        return ReservationSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['patch'], url_path='cancel')
    def cancel_reservation(self, request, pk=None):
        reservation = self.get_object()

        if reservation.status == 'cancelled':
            return Response({"detail": "Reserva já cancelada."}, status=400)

        if not reservation.can_cancel():
            return Response({"detail": "Prazo para cancelamento expirado."}, status=400)

        reservation.status = 'cancelled'
        from django.utils.timezone import now
        reservation.cancelled_at = now()
        reservation.save()

        return Response({"detail": "Reserva cancelada com sucesso."})

class OwnerDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsOwner]

    def get(self, request):
        user = request.user
        locations = Location.objects.filter(owner=user)

        total_locations = locations.count()

        total_reservations = Reservation.objects.filter(location__in=locations).count()

        upcoming_reservations = Reservation.objects.filter(
            location__in=locations,
            date__gte=date.today(),
            status='confirmed'
        ).count()

        reservations_per_location = Reservation.objects.filter(
            location__in=locations
        ).values('location__name').annotate(count=Count('id'))

        return Response({
            'total_locations': total_locations,
            'total_reservations': total_reservations,
            'upcoming_reservations': upcoming_reservations,
            'reservations_per_location': reservations_per_location,
        })
    
class CustomerReservationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reservations = Reservation.objects.filter(user=request.user).order_by('-date', '-start_time')
        serializer = ReservationSerializer(reservations, many=True)
        return Response(serializer.data)

class UserTypeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        groups = request.user.groups.values_list('name', flat=True)
        return Response({"groups": list(groups)})
