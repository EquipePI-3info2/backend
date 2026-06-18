from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from core.models import User


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'telefone', 'is_active', 'is_staff', 'profile_photo']
        # is_active/is_staff só podem ser alterados pelo Django Admin,
        # nunca via API — evita escalonamento de privilégio por um cliente.
        read_only_fields = ['id', 'is_active', 'is_staff']


class UserRegistrationSerializer(ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'telefone', 'password']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class ProfilePhotoSerializer(ModelSerializer):
    """
    Serializer dedicado ao upload/remoção da foto de perfil.
    Usado isoladamente (não pelo UserSerializer geral) para que o endpoint
    de foto não exponha nem permita alterar os demais campos do usuário.
    """

    class Meta:
        model = User
        fields = ['profile_photo']
