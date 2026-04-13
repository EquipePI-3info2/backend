from rest_framework.viewsets import ModelViewSet

from core.models import Sabor
from core.serializers import SaborSerializer


class SaborViewSet(ModelViewSet):
    queryset = Sabor.objects.all()
    serializer_class = SaborSerializer
