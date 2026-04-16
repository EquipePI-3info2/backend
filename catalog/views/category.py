from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from ..models import Category
from ..serializers import CategorySerializer, CategoryWriteSerializer, ProductSerializer
from ..permissions import IsAdminOrReadOnly


@extend_schema_view(
    list=extend_schema(summary="Listar categorias"),
    retrieve=extend_schema(summary="Detalhe da categoria"),
    create=extend_schema(summary="Criar categoria [admin]"),
    partial_update=extend_schema(summary="Editar categoria [admin]"),
    destroy=extend_schema(summary="Remover categoria [admin]"),
)
class CategoryViewSet(viewsets.ModelViewSet):
    """
    GET    /api/categories/                  → lista (público)
    GET    /api/categories/{slug}/           → detalhe (público)
    GET    /api/categories/{slug}/products/  → produtos da categoria (público)
    POST   /api/categories/                  → criar (admin)
    PATCH  /api/categories/{slug}/           → editar (admin)
    DELETE /api/categories/{slug}/           → remover (admin)
    """
    queryset             = Category.objects.all()
    permission_classes   = [IsAdminOrReadOnly]
    lookup_field         = "slug"
    filter_backends      = [filters.OrderingFilter]
    ordering_fields      = ["order", "name", "created_at"]
    ordering             = ["order", "name"]
    http_method_names    = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            qs = qs.filter(is_active=True)
        return qs

    def get_serializer_class(self):
        if self.request.method in ("POST", "PATCH"):
            return CategoryWriteSerializer
        return CategorySerializer

    @extend_schema(summary="Produtos desta categoria")
    @action(detail=True, methods=["get"], url_path="products")
    def products(self, request, slug=None):
        """GET /api/categories/{slug}/products/"""
        category = self.get_object()
        qs = (
            category.products
            .filter(is_active=True)
            .select_related("category")
            .order_by("-is_featured", "name")
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            s = ProductSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(s.data)
        s = ProductSerializer(qs, many=True, context={"request": request})
        return Response(s.data)
