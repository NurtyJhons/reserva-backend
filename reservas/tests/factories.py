import factory
from django.contrib.auth.models import User, Group
from reservas.models import Location, Reservation, UserProfile, LocationImage
from datetime import datetime, timedelta

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'password123')

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            # Para grupos passados como lista de strings
            if isinstance(extracted, (list, tuple)):
                for group_name in extracted:
                    group, _ = Group.objects.get_or_create(name=group_name)
                    self.groups.add(group)
            # Para grupos passados como objetos Group
            else:
                self.groups.add(extracted)

class UserProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserProfile

    user = factory.SubFactory(UserFactory)
    phone = "11999999999"
    cpf = "12345678901"

class LocationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Location

    owner = factory.SubFactory(UserFactory)
    name = "Local de Teste"
    description = "Descrição do local"
    address = "Rua Teste, 123"
    price_per_hour = 50.00
    is_active = True

class ReservationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Reservation

    user = factory.SubFactory(UserFactory)
    location = factory.SubFactory(LocationFactory)
    date = factory.LazyFunction(datetime.now().date)
    start_time = datetime.now().time()
    end_time = (datetime.now() + timedelta(hours=2)).time()
    status = 'confirmed'