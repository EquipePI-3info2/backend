from rest_framework.serializers import ModelSerializer

from core.models import Sabor


class SaborSerializer(ModelSerializer):
    class Meta:
        model = Sabor
        fields = '__all__'
