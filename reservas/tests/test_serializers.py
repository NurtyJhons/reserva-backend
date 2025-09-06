import pytest
from rest_framework.exceptions import ValidationError
from reservas.serializers import ReservationCreateSerializer
from reservas.tests.factories import ReservationFactory, LocationFactory, UserFactory

@pytest.mark.django_db
def test_reservation_serializer_validates_time_conflict():
    user = UserFactory()
    owner = UserFactory()
    location = LocationFactory(
        owner=owner,
        operating_hours_start='08:00',  # Mantém padrão ou ajuste conforme necessário
        operating_hours_end='23:30'     # Estende até 23:30 para incluir o teste
    )

    # Dados válidos (dentro do horário de funcionamento)
    from datetime import datetime, timedelta
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Cria uma reserva existente
    ReservationFactory(
        location=location,
        date=tomorrow,
        start_time="14:00",
        end_time="16:00",
        status='confirmed'
    )

    # Tenta criar uma reserva conflitante
    data = {
        "location": location.id,
        "date": tomorrow,
        "start_time": "15:00",
        "end_time": "17:00",
        "payment_method": "pix"
    }
    serializer = ReservationCreateSerializer(data=data, context={'request': type('obj', (), {'user': user})})
    
    with pytest.raises(ValidationError) as excinfo:
        serializer.is_valid(raise_exception=True)
    assert "Conflito com outra reserva" in str(excinfo.value.detail)