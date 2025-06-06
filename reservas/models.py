from django.db import models
from django.contrib.auth.models import User
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

class Reservation(models.Model):
    STATUS_CHOICES = (
        ('confirmed', 'Confirmada'),
        ('cancelled', 'Cancelada'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='confirmed')
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

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