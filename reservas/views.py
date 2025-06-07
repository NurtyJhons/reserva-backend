from rest_framework import generics, viewsets, status, permissions
from .serializers import UserRegistrationSerializer, LocationSerializer, LocationCreateSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny, IsAuthenticated
from .models import Location, Reservation, Payment, LocationImage
from .permissions import IsOwnerOrReadOnly, IsReservationOwnerOrReadOnly, IsOwner
from rest_framework.response import Response
from rest_framework.decorators import action
from .serializers import ReservationSerializer, ReservationCreateSerializer, PaymentSerializer, LocationImageSerializer
from rest_framework.views import APIView
from django.utils.timezone import now, make_aware
from datetime import date, datetime, timedelta
from django.db.models import Count
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.filter(is_active=True)
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.action == 'create':
            return LocationCreateSerializer
        return LocationSerializer

    def perform_create(self, serializer):
        serializer.save()

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.groups.filter(name='owners').exists():
            return Location.objects.filter(owner=self.request.user)
        return Location.objects.filter(is_active=True)
    
class LocationImageUploadView(generics.CreateAPIView):
    serializer_class = LocationImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        location_id = self.request.data.get('location')
        location = Location.objects.get(id=location_id, owner=self.request.user)
        serializer.save(location=location)

class LocationImageDeleteView(generics.DestroyAPIView):
    queryset = LocationImage.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Garante que o owner só delete imagens dos seus próprios locais
        return LocationImage.objects.filter(location__owner=self.request.user)

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    permission_classes = [IsAuthenticated, IsReservationOwnerOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

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

    # def perform_create(self, serializer):
    #    serializer.save(user=self.request.user)

    @action(detail=True, methods=['patch'], url_path='cancel')
    def cancel_reservation(self, request, pk=None):
        reservation = self.get_object()

        if reservation.status == 'cancelled':
            return Response({"detail": "Reserva já cancelada."}, status=400)

        if not reservation.can_cancel():
            return Response({"detail": "Prazo para cancelamento expirado."}, status=400)
        
        # Atualiza status da reserva
        reservation.status = 'cancelled'
        reservation.cancelled_at = now()
        reservation.save()

        try:
            payment = reservation.payment
        except Payment.DoesNotExist:
            payment = None

        if payment and payment.status == 'pago':
            # Constrói datetime da reserva
            inicio_reserva = datetime.combine(reservation.date, reservation.start_time)
            inicio_reserva = make_aware(inicio_reserva)

            # Se ainda faltam mais de 24h, reembolsa
            if inicio_reserva - now() >= timedelta(hours=24):
                payment.status = 'reembolsado'
                payment.reembolsado_em = now()
                payment.save()

                return Response({
                    "detail": "Reserva cancelada e reembolso realizado com sucesso."
                })

        return Response({"detail": "Reserva cancelada com sucesso. Sem reembolso por estar fora do prazo."})

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

class PaymentCreateView(generics.CreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated, JSONParser]