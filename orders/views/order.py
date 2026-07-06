from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from orders.models import Order
from orders.serializers import (
    OrderCreateSerializer,
    OrderSerializer,
    OrderUpdateSerializer,
)


@extend_schema_view(
    list=extend_schema(summary="Listar pedidos"),
    retrieve=extend_schema(summary="Detalhes do pedido"),
    create=extend_schema(summary="Criar pedido"),
    partial_update=extend_schema(summary="Atualizar pedido"),
    destroy=extend_schema(summary="Excluir pedido"),
)
class OrderViewSet(viewsets.ModelViewSet):
    """
    CRUD de pedidos.

    Administradores:
        - possuem acesso a todos os pedidos.

    Usuários comuns:
        - visualizam apenas os próprios pedidos.
    """

    permission_classes = [IsAuthenticated]

    http_method_names = [
        "get",
        "post",
        "patch",
        "delete",
        "head",
        "options",
    ]

    def get_queryset(self):
        queryset = (
            Order.objects
            .select_related(
                "user",
                "payment",
            )
            .prefetch_related(
                "items",
                "items__product",
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

    @extend_schema(
        summary="Pedidos do usuário autenticado",
    )
    @action(
        detail=False,
        methods=["get"],
    )
    def me(self, request):
        """
        Lista apenas os pedidos do usuário autenticado.
        """

        queryset = self.filter_queryset(
            self.get_queryset()
        )

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(
                page,
                many=True,
            )
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            queryset,
            many=True,
        )

        return Response(serializer.data)

    @extend_schema(
        summary="Último pedido do usuário",
    )
    @action(
        detail=False,
        methods=["get"],
    )
    def latest(self, request):
        """
        Retorna o pedido mais recente do usuário autenticado.
        """

        order = self.get_queryset().first()

        if order is None:
            return Response(
                {"detail": "Nenhum pedido encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(order)

        return Response(serializer.data)
