from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    cpf = models.CharField(max_length=14)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_owner(self):
        return self.user.groups.filter(name='owners').exists()

    @property
    def is_customer(self):
        return self.user.groups.filter(name='customers').exists()

class Location(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    address = models.CharField(max_length=255)
    price_per_hour = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    operating_hours_start = models.TimeField(default='08:00')
    operating_hours_end = models.TimeField(default='18:00')
    cancellation_hours = models.PositiveIntegerField(default=24)
    max_duration = models.PositiveIntegerField(default=4)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.address}"
    
class LocationImage(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(
        upload_to='location_images/',
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Imagem de {self.location.name}"

class Reservation(models.Model):
    class Status(models.TextChoices):
        PENDENTE = 'pendente', 'Pendente'
        CONFIRMADA = 'confirmed', 'Confirmada'
        CANCELADA = 'cancelled', 'Cancelada'

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDENTE)

    def can_cancel(self):
        """Verifica se a reserva pode ser cancelada com base na regra de antecedência"""
        if self.status == 'cancelled':
            return False
        from datetime import datetime, timedelta, time
        from django.utils.timezone import make_aware

        location_cancel_limit = self.location.cancellation_hours
        reservation_datetime = datetime.combine(self.date, self.start_time)
        now = datetime.now()
        return reservation_datetime - timedelta(hours=location_cancel_limit) > now

    def __str__(self):
        return f"{self.location.name} - {self.date} {self.start_time}-{self.end_time}"
    
class Payment(models.Model):
    class PaymentMethod(models.TextChoices):
        PIX = 'pix', 'PIX'
        BOLETO = 'boleto', 'Boleto'
        CARTAO = 'cartao', 'Cartão'

    class PaymentStatus(models.TextChoices):
        PENDENTE = 'pendente', 'Pendente'
        PAGO = 'pago', 'Pago'
        REEMBOLSADO = 'reembolsado', 'Reembolsado'

    reservation = models.OneToOneField("Reservation", on_delete=models.CASCADE, related_name="payment")
    method = models.CharField(max_length=10, choices=PaymentMethod.choices)
    status = models.CharField(max_length=15, choices=PaymentStatus.choices, default=PaymentStatus.PENDENTE)
    valor = models.DecimalField(max_digits=8, decimal_places=2)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    reembolsado_em = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Pagamento {self.id} - {self.get_method_display()} - {self.status}"
