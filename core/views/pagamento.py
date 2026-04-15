from rest_framework.viewsets import ModelViewSet

from core.models import Pagamento
from core.serializers import PagamentoSerializer


class PagamentoViewSet(ModelViewSet):
    queryset = Pagamento.objects.all()
    serializer_class = PagamentoSerializer
