import pytest
from datetime import datetime, timedelta, time
from django.utils import timezone
from reservas.models import Reservation, Location
from reservas.tests.factories import ReservationFactory, LocationFactory

@pytest.mark.django_db
def test_reservation_can_cancel():
    # Cria uma reserva com horário cancelável (mais de 24h no futuro)
    future_time = timezone.now() + timedelta(hours=25)
    reservation = ReservationFactory(
        date=future_time.date(),
        start_time=time(14, 0),
        status='confirmed'
    )
    assert reservation.can_cancel() is True

    # Reserva no passado não pode ser cancelada
    past_time = timezone.now() - timedelta(days=1)
    reservation = ReservationFactory(
        date=past_time.date(),
        start_time=time(14, 0),
        status='confirmed'
    )
    assert reservation.can_cancel() is False

@pytest.mark.django_db
def test_location_str():
    location = LocationFactory(name="Sala de Reuniões")
    assert str(location) == "Sala de Reuniões - Rua Teste, 123"