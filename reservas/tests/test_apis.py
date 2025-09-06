import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from reservas.tests.factories import UserFactory, LocationFactory

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_client(api_client):
    user = UserFactory()
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client

@pytest.mark.django_db
def test_location_list_api(authenticated_client):
    LocationFactory.create_batch(3)
    response = authenticated_client.get('/api/locations/')
    assert response.status_code == 200
    assert len(response.data) == 3  # Paginação pode alterar isso

@pytest.mark.django_db
def test_create_reservation(authenticated_client):
    # Configuração
    owner = UserFactory()
    # Cria local com horário de funcionamento que inclua 20:00-23:00
    location = LocationFactory(
        owner=owner,
        operating_hours_start='08:00',  # Mantém padrão ou ajuste conforme necessário
        operating_hours_end='23:30'     # Estende até 23:30 para incluir o teste
    )
    
    # Dados válidos (dentro do horário de funcionamento)
    from datetime import datetime, timedelta
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    data = {
        "location": location.id,
        "date": tomorrow,
        "start_time": "20:00",  # Agora dentro do horário
        "end_time": "22:00",    # Termina antes do fechamento
        "payment_method": "pix"
    }
    
    # Execução
    response = authenticated_client.post('/api/reservations/', data, format='json')
    
    # Verificação
    assert response.status_code == 201, response.data
    assert 'id' in response.data  # Verifica se a reserva foi criada com ID
    assert response.data['location'] == location.id  # Verifica associação correta
    assert response.data['status'] == 'pendente'