from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from core.models import User


class UserSerializer(ModelSerializer):
    profile_photo_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'name',
            'telefone',
            'is_active',
            'is_staff',
            'profile_photo_url',
        ]
        read_only_fields = ['id', 'is_active', 'is_staff']

    def get_profile_photo_url(self, obj):
        request = self.context.get('request')

        if not obj.profile_photo:
            return None

        if request:
            return request.build_absolute_uri(obj.profile_photo.url)

        return obj.profile_photo.url


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
