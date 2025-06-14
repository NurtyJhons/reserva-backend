from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import UserProfile, Reservation, Location, Payment, LocationImage
from django.utils import timezone
from datetime import timedelta

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    user_type = serializers.ChoiceField(
        choices=[('customer', 'Customer'), ('owner', 'Owner')],
        write_only=True
    )
    phone = serializers.CharField(write_only=True)
    cpf = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'user_type', 'phone', 'cpf']

    def create(self, validated_data):
        user_type = validated_data.pop('user_type')
        phone = validated_data.pop('phone')
        cpf = validated_data.pop('cpf')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        group = Group.objects.get_or_create(name=f"{user_type}s")[0]
        user.groups.add(group)

        # cria o perfil manualmente
        UserProfile.objects.create(user=user, phone=phone, cpf=cpf)

        return user

class LocationSerializer(serializers.ModelSerializer):

    images = serializers.SerializerMethodField()

    def get_images(self, obj):
        return [image.image_url for image in obj.images.all()]
    
    class Meta:
        model = Location
        fields = [
            'id',
            'name',
            'description',
            'address',
            'price_per_hour',
            'operating_hours_start',
            'operating_hours_end',
            'cancellation_hours',
            'max_duration',
            'is_active',
            'created_at',
            'owner',
            'images',
        ]
        read_only_fields = ['owner', 'id', 'is_active', 'created_at']

    def get_images(self, obj):
        request = self.context.get('request')
        return [
            request.build_absolute_uri(image.image.url)
            for image in obj.images.all()
            if image.image
        ]
    
class LocationImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = LocationImage
        fields = ['id', 'image', 'image_url', 'uploaded_at']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url)
        return None
    
class LocationCreateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True
    )

    class Meta:
        model = Location
        fields = [
            'name', 'description', 'address', 'price_per_hour',
            'operating_hours_start', 'operating_hours_end',
            'cancellation_hours', 'max_duration', 'images'
        ]

    def create(self, validated_data):
        images = validated_data.pop('images')
        owner = self.context['request'].user
        location = Location.objects.create(owner=owner, **validated_data)

        for image in images:
            LocationImage.objects.create(location=location, image=image)

        return location
    
class ReservationSerializer(serializers.ModelSerializer):
    location_name = serializers.CharField(source='location.name', read_only=True)
    location_address = serializers.CharField(source='location.address', read_only=True)
    location_description = serializers.CharField(source='location.description', read_only=True)
    local_cancelado = serializers.SerializerMethodField()
    location_images = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = [
            'id',
            'location',
            'location_name',
            'location_address',
            'location_description',
            'date',
            'start_time',
            'end_time',
            'status',
            'cancelled_at',
            'created_at',
            'local_cancelado',
            'location_images',
        ]

    def get_local_cancelado(self, obj):
        return not obj.location.is_active
    
    def get_location_images(self, obj):
        return [img.image.url for img in obj.location.images.all()]

class ReservationCreateSerializer(serializers.ModelSerializer):
    payment_method = serializers.ChoiceField(choices=Payment.PaymentMethod.choices, write_only=True)
    pagamento_status = serializers.ChoiceField(choices=Payment.PaymentStatus.choices, write_only=True, required=False)

    class Meta:
        model = Reservation
        fields = ['location', 'date', 'start_time', 'end_time', 'payment_method', 'pagamento_status']

    def validate(self, data):
        from datetime import datetime, timedelta

        user = self.context['request'].user
        location = data['location']
        date = data['date']
        start_time = data['start_time']
        end_time = data['end_time']

        if start_time >= end_time:
            raise serializers.ValidationError("O horário de início deve ser anterior ao de término.")

        # 🔸 Verifica se horário está dentro do funcionamento do local
        if start_time < location.operating_hours_start or end_time > location.operating_hours_end:
            raise serializers.ValidationError("Horário fora do horário de funcionamento do local.")

        # 🔸 Verifica duração máxima
        duration = datetime.combine(date, end_time) - datetime.combine(date, start_time)
        max_duration = timedelta(hours=location.max_duration)
        if duration > max_duration:
            raise serializers.ValidationError(f"Duração excede o máximo permitido de {location.max_duration} horas.")

        # 🔸 Verifica se data/hora está no futuro
        now = datetime.now()
        if datetime.combine(date, start_time) <= now:
            raise serializers.ValidationError("Não é possível fazer reservas no passado.")

        # 🔸 Verifica conflitos com outras reservas
        conflicts = Reservation.objects.filter(
            location=location,
            date=date,
            status='confirmed',
        ).filter(
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        if conflicts.exists():
            raise serializers.ValidationError("Conflito com outra reserva existente neste horário.")

        return data

    def create(self, validated_data):
        user = self.context['request'].user
        payment_method = validated_data.pop('payment_method')
        pagamento_status = validated_data.pop('pagamento_status', Payment.PaymentStatus.PENDENTE)

        reserva = Reservation.objects.create(user=user, status=Reservation.Status.PENDENTE, **validated_data)

        valor = reserva.location.price_per_hour * ((reserva.end_time.hour - reserva.start_time.hour))
        pagamento = Payment.objects.create(
            reservation=reserva,
            method=payment_method,
            status=pagamento_status,
            valor=valor
        )

        if pagamento.status == Payment.PaymentStatus.PAGO:
            reserva.status = Reservation.Status.CONFIRMADA
            reserva.save()

        return reserva

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['status', 'criado_em', 'atualizado_em']
