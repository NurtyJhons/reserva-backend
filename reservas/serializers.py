from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import UserProfile, Reservation, Location

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
            'owner'
        ]
        read_only_fields = ['owner', 'id', 'is_active', 'created_at']

class ReservationSerializer(serializers.ModelSerializer):
    location_name = serializers.CharField(source='location.name', read_only=True)

    class Meta:
        model = Reservation
        fields = [
            'id',
            'location',
            'location_name',
            'date',
            'start_time',
            'end_time',
            'status',
            'cancelled_at',
            'created_at',
        ]

class ReservationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ['location', 'date', 'start_time', 'end_time']

    def validate(self, data):
        from datetime import datetime, timedelta

        user = self.context['request'].user
        location = data['location']
        date = data['date']
        start_time = data['start_time']
        end_time = data['end_time']

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
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
