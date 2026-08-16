from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, viewsets

from ..models import Flavor
from ..permissions import IsAdminOrReadOnly
from ..serializers import FlavorSerializer, FlavorWriteSerializer


@extend_schema_view(
    list=extend_schema(summary="Listar sabores"),
    retrieve=extend_schema(summary="Detalhe do sabor"),
    create=extend_schema(summary="Criar sabor [admin]"),
    partial_update=extend_schema(summary="Editar sabor [admin]"),
    destroy=extend_schema(summary="Remover sabor [admin]"),
)
class FlavorViewSet(viewsets.ModelViewSet):
    queryset = Flavor.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            qs = qs.filter(is_active=True)
        return qs

    def get_serializer_class(self):
        if self.request.method in {"POST", "PATCH"}:
            return FlavorWriteSerializer
        return FlavorSerializer
