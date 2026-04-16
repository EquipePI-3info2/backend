from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view

from ..models import Product
from ..serializers import ProductSerializer, ProductAdminSerializer, ProductWriteSerializer
from ..permissions import IsAdminOrReadOnly
from ..filters import ProductFilter


@extend_schema_view(
    list=extend_schema(summary="Listar produtos"),
    retrieve=extend_schema(summary="Detalhe do produto"),
    create=extend_schema(summary="Criar produto [admin]"),
    partial_update=extend_schema(summary="Editar produto [admin]"),
    destroy=extend_schema(summary="Remover produto [admin]"),
)
class ProductViewSet(viewsets.ModelViewSet):
    """
    Filtros disponíveis:
      ?category=cookies          → por slug de categoria
      ?price_min=5&price_max=15  → faixa de preço
      ?is_featured=true          → somente destaques
      ?in_stock=true             → somente em estoque
      ?search=red+velvet         → busca em nome e descrição
      ?ordering=price            → ordenação (use - para decrescente)

    Admin recebe campos adicionais: cost_price, gross_margin_pct, gross_profit.
    """
    permission_classes = [IsAdminOrReadOnly]
    lookup_field       = "slug"
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class    = ProductFilter
    search_fields      = ["name", "description", "flavor", "category__name"]
    ordering_fields    = ["price", "name", "created_at", "stock"]
    ordering           = ["-is_featured", "name"]
    http_method_names  = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        qs = Product.objects.select_related("category").all()
        if not self.request.user.is_staff:
            # Visitante só vê produtos ativos de categorias ativas
            qs = qs.filter(is_active=True, category__is_active=True)
        return qs

    def get_serializer_class(self):
        if self.request.method in ("POST", "PATCH"):
            return ProductWriteSerializer
        if self.request.user.is_staff:
            return ProductAdminSerializer
        return ProductSerializer
