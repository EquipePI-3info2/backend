from django.db.models import Prefetch
from django.db.models.deletion import ProtectedError
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.response import Response

from ..models import Kit, KitItem
from ..permissions import IsAdminOrReadOnly
from ..serializers import KitAdminSerializer, KitSerializer, KitWriteSerializer


@extend_schema_view(
    list=extend_schema(summary="Listar kits promocionais"),
    retrieve=extend_schema(summary="Detalhe do kit promocional"),
    create=extend_schema(summary="Criar kit [admin]"),
    partial_update=extend_schema(summary="Editar kit [admin]"),
    destroy=extend_schema(summary="Remover kit [admin]"),
)
class KitViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description", "items__product__name"]
    ordering_fields = ["promotional_price", "name", "created_at"]
    ordering = ["-is_featured", "name"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        item_queryset = KitItem.objects.select_related(
            "product",
            "product__category",
            "product__flavor",
        ).order_by("id")
        qs = Kit.objects.prefetch_related(Prefetch("items", queryset=item_queryset)).all()
        if not self.request.user.is_staff:
            qs = qs.filter(is_active=True)
        return qs.distinct()

    def get_serializer_class(self):
        if self.request.method in {"POST", "PATCH"}:
            return KitWriteSerializer
        if self.request.user.is_staff:
            return KitAdminSerializer
        return KitSerializer

    def destroy(self, request, *args, **kwargs):
        kit = self.get_object()
        try:
            kit.delete()
        except ProtectedError:
            return Response(
                {
                    "detail": (
                        "Este kit já aparece em pedidos e não pode ser excluído. "
                        "Desative o kit para removê-lo da vitrine."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
