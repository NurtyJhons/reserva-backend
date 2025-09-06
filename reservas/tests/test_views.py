import pytest
from django.contrib.auth.models import Group
from rest_framework.test import APIRequestFactory
from reservas.views import LocationViewSet
from reservas.tests.factories import UserFactory, LocationFactory
from rest_framework.exceptions import PermissionDenied

from rest_framework.test import force_authenticate  # Adicione este import

@pytest.mark.django_db
def test_only_owner_can_edit_location():
    # Cria grupos
    owners_group = Group.objects.create(name='owners')
    customers_group = Group.objects.create(name='customers')
    
    # Cria usuários
    owner = UserFactory()
    owner.groups.add(owners_group)
    
    customer = UserFactory()
    customer.groups.add(customers_group)
    
    # Cria local
    location = LocationFactory(owner=owner)

    # Configura a requisição PATCH autenticada
    factory = APIRequestFactory()
    request = factory.patch(
        f'/locations/{location.id}/',
        {'name': 'Nome Proibido'},
        format='json'
    )
    force_authenticate(request, user=customer)  # Autentica o usuário customer
    
    # Chama a view
    view = LocationViewSet.as_view({'patch': 'partial_update'})
    response = view(request, pk=location.id)
    
    # Agora deve retornar 403 (Forbidden) ao invés de 401 (Unauthorized)
    assert response.status_code == 403, f"Esperado 403, recebido {response.status_code}. Resposta: {response.data}"

@pytest.mark.django_db
def test_unauthenticated_cannot_edit_location():
    owner = UserFactory()
    location = LocationFactory(owner=owner)

    factory = APIRequestFactory()
    request = factory.patch(
        f'/locations/{location.id}/',
        {'name': 'Nome Proibido'},
        format='json'
    )
    # Não usa force_authenticate
    
    view = LocationViewSet.as_view({'patch': 'partial_update'})
    response = view(request, pk=location.id)
    
    assert response.status_code == 401  # Não autenticado