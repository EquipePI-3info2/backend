from rest_framework.serializers import ModelSerializer

from core.models import Pagamento


class PagamentoSerializer(ModelSerializer):
    class Meta:
        model = Pagamento
        fields = '__all__'
