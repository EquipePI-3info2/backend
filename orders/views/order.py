from django.db.models import IntegerField, Prefetch, Sum, Value
from django.db.models.functions import Coalesce
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from orders.models import Order, OrderItem
from orders.serializers import (
    OrderCreateSerializer,
    OrderSerializer,
    OrderUpdateSerializer,
)
from orders.services import OrderServiceError, cancel_order


@extend_schema_view(
    list=extend_schema(summary="Listar pedidos"),
    retrieve=extend_schema(summary="Detalhes do pedido"),
    create=extend_schema(summary="Criar pedido"),
    partial_update=extend_schema(summary="Atualizar status do pedido [admin]"),
)
class OrderViewSet(viewsets.ModelViewSet):
    # Queryset base necessário para o drf-spectacular identificar o model.
    queryset = Order.objects.none()
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_permissions(self):
        if self.action == "partial_update":
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()

        item_queryset = OrderItem.objects.select_related(
            "product",
            "product__category",
            "product__flavor",
        ).order_by("id")

        queryset = (
            Order.objects.select_related("user", "payment")
            .prefetch_related(Prefetch("items", queryset=item_queryset))
            .annotate(
                total_items_count=Coalesce(
                    Sum("items__quantity"),
                    Value(0),
                    output_field=IntegerField(),
                )
            )
            .order_by("-created_at")
        )

        if self.request.user.is_staff:
            return queryset
        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        if self.action == "partial_update":
            return OrderUpdateSerializer
        return OrderSerializer

    @extend_schema(summary="Pedidos do usuário autenticado")
    @action(detail=False, methods=["get"])
    def me(self, request):
        queryset = self.filter_queryset(
            self.get_queryset().filter(user=request.user)
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = OrderSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)
        serializer = OrderSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)

    @extend_schema(summary="Último pedido do usuário autenticado")
    @action(detail=False, methods=["get"])
    def latest(self, request):
        order = self.get_queryset().filter(user=request.user).first()
        if order is None:
            return Response(
                {"detail": "Nenhum pedido encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(OrderSerializer(order, context={"request": request}).data)

    @extend_schema(summary="Cancelar pedido")
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        try:
            order = cancel_order(order=order, actor=request.user)
        except OrderServiceError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order = self.get_queryset().get(pk=order.pk)
        return Response(OrderSerializer(order, context={"request": request}).data)
