from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from orders.models import Payment
from orders.serializers import PaymentSerializer, PaymentStatusUpdateSerializer


@extend_schema_view(
    list=extend_schema(summary="Listar pagamentos"),
    retrieve=extend_schema(summary="Detalhar pagamento"),
    partial_update=extend_schema(summary="Atualizar status do pagamento [admin]"),
)
class PaymentViewSet(viewsets.ModelViewSet):
    # Queryset base necessário para o drf-spectacular identificar o model.
    queryset = Payment.objects.none()
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    def get_permissions(self):
        if self.action == "partial_update":
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Payment.objects.none()

        queryset = Payment.objects.select_related("order", "order__user").order_by(
            "-created_at"
        )
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(order__user=self.request.user)

    def get_serializer_class(self):
        if self.action == "partial_update":
            return PaymentStatusUpdateSerializer
        return PaymentSerializer
