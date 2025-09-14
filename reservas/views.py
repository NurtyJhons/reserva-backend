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
from datetime import date, datetime, timedelta, time
from django.db.models import Count
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def login_view(request):
    return render(request, 'reservas/auth/login.html')

def register_view(request):
    return render(request, 'reservas/auth/register.html')

@login_required
def owner_dashboard(request):
    return render(request, 'reservas/dashboards/owner.html')  

@login_required
def create_location(request):
    return render(request, 'reservas/locations/create.html')

@login_required
def create_reservation(request):
    return render(request, 'reservas/reservations/create.html')

@login_required
def list_reservations(request):
    return render(request, 'reservas/reservations/list.html')

class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.filter(is_active=True)
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    serializer_class = LocationSerializer
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
    
    @action(detail=True, methods=['get'], url_path='available-slots')
    def available_slots(self, request, pk=None): 
        try:
            location = self.get_object()
        except Location.DoesNotExist:
            return Response({"detail": "Local não encontrado."}, status=404)

        date_str = request.query_params.get('date')
        if not date_str:
            return Response({"detail": "Data não fornecida."}, status=400)

        try:
            query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"detail": "Formato de data inválido. Use YYYY-MM-DD."}, status=400)
        
        # Buscar reservas ativas (confirmadas e pendentes) para o local e data específica
        existing_reservations = Reservation.objects.filter(
            location=location, 
            date=query_date
        ).exclude(status='cancelled')  # Exclui apenas as canceladas
        
        reserved_slots = set()
        for res in existing_reservations:
            # Marcar todos os horários entre start_time e end_time como ocupados
            start_hour = res.start_time.hour
            end_hour = res.end_time.hour
            
            # Importante: incluir TODAS as horas do período da reserva
            # Se reserva é de 15:00 até 22:00, ocupar slots: 15, 16, 17, 18, 19, 20, 21
            reserved_slots.update(range(start_hour, end_hour))
        
        # Considerar horário de funcionamento do local
        start_operating = location.operating_hours_start.hour
        end_operating = location.operating_hours_end.hour
        
        # Incluir a última hora se o local funciona até ela
        # Ex: se funciona até 23:00, deve mostrar slot 23:00
        if location.operating_hours_end.minute >= 0:
            end_operating += 1
        
        # Gerar horários disponíveis dentro do horário de funcionamento
        operating_slots = range(start_operating, end_operating)
        available_slots = [f"{h:02d}:00" for h in operating_slots if h not in reserved_slots]

        # Debug: adicionar informações úteis na resposta
        debug_info = {
            "total_reservations": len(existing_reservations),
            "reserved_hours": sorted(list(reserved_slots)),
            "operating_range": f"{start_operating}:00 - {end_operating-1}:00"
        }

        return Response({
            "available_slots": available_slots,
            "debug": debug_info,  # Remover depois dos testes
            "message": "Nenhum horário disponível hoje." if not available_slots else f"{len(available_slots)} horários disponíveis."
        })
    
    @action(detail=True, methods=['patch'], url_path='cancel')
    def cancel_location(self, request, pk=None):
        location = self.get_object()

        # Apenas o proprietário pode cancelar
        if location.owner != request.user:
            return Response({'detail': 'Permissão negada.'}, status=403)

        location.is_active = False
        location.save()
        return Response({'detail': 'Local cancelado com sucesso.'}, status=200)
    
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