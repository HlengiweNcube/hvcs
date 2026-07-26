"""
DRF serializers for the HVCS API.

Each serializer maps a model to its JSON representation used by the React
front-end.  Write operations (create/update) include validation so the API
remains the single source of truth for business rules.
"""

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Caregiver, Client, User, Visit


# ---------------------------------------------------------------------------
# User / Auth
# ---------------------------------------------------------------------------

class UserSerializer(serializers.ModelSerializer):
    """Read-only profile info returned after login."""

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role')
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    """Allow a new caregiver to self-register via the API."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, label='Confirm password')
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    qualifications = serializers.CharField(max_length=255, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name',
            'password', 'password2', 'phone', 'qualifications',
        )

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({'password2': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        phone = validated_data.pop('phone', '')
        qualifications = validated_data.pop('qualifications', '')
        password = validated_data.pop('password')

        user = User(**validated_data)
        user.set_password(password)
        user.role = User.Role.CAREGIVER
        user.save()

        Caregiver.objects.create(
            user=user,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=phone,
            qualifications=qualifications,
        )
        return user


# ---------------------------------------------------------------------------
# Caregiver
# ---------------------------------------------------------------------------

class CaregiverSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Caregiver
        fields = ('id', 'user', 'first_name', 'last_name', 'phone', 'qualifications', 'is_active')


class CaregiverWriteSerializer(serializers.ModelSerializer):
    """Used by admins to create/update a caregiver (and their linked User)."""

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])

    class Meta:
        model = Caregiver
        fields = (
            'username', 'email', 'password',
            'first_name', 'last_name', 'phone', 'qualifications', 'is_active',
        )

    def create(self, validated_data):
        username = validated_data.pop('username')
        email = validated_data.pop('email', '')
        password = validated_data.pop('password')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=User.Role.CAREGIVER,
        )
        return Caregiver.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        username = validated_data.pop('username', None)
        email = validated_data.pop('email', None)
        password = validated_data.pop('password', None)

        if username:
            instance.user.username = username
        if email is not None:
            instance.user.email = email
        if password:
            instance.user.set_password(password)
        instance.user.first_name = validated_data.get('first_name', instance.user.first_name)
        instance.user.last_name = validated_data.get('last_name', instance.user.last_name)
        instance.user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ('id', 'first_name', 'last_name', 'address', 'contact_phone', 'care_needs', 'is_active')


# ---------------------------------------------------------------------------
# Visit
# ---------------------------------------------------------------------------

class VisitSerializer(serializers.ModelSerializer):
    caregiver_name = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()

    class Meta:
        model = Visit
        fields = (
            'id', 'caregiver', 'caregiver_name',
            'client', 'client_name',
            'scheduled_date', 'scheduled_time', 'status', 'notes',
            'check_in_lat', 'check_in_lng', 'check_in_time', 'check_out_time',
            'created_at',
        )
        read_only_fields = ('check_in_lat', 'check_in_lng', 'check_in_time', 'check_out_time', 'created_at')

    def get_caregiver_name(self, obj):
        return str(obj.caregiver)

    def get_client_name(self, obj):
        return str(obj.client)


class VisitCheckinSerializer(serializers.Serializer):
    """Payload for the caregiver check-in action."""
    lat = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    lng = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------

class ManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_active')


class ManagerCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.role = User.Role.MANAGER
        user.save()
        return user
