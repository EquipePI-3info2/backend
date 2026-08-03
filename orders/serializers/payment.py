from decimal import Decimal

from rest_framework import serializers

from orders.models import Payment
from orders.services import OrderServiceError, update_payment_status


class PaymentSerializer(serializers.ModelSerializer):
    method_display = serializers.CharField(source="get_method_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    order_code = serializers.SerializerMethodField()

    def get_order_code(self, obj: Payment) -> str | None:
        order = getattr(obj, "order", None)
        return order.code if order is not None else None

    class Meta:
        model = Payment
        fields = [
            "id",
            "order_code",
            "method",
            "method_display",
            "status",
            "status_display",
            "amount_paid",
            "transaction_id",
            "paid_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class PaymentStatusUpdateSerializer(serializers.ModelSerializer):
    amount_paid = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.00"),
        required=False,
    )
    transaction_id = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Payment
        fields = ["status", "amount_paid", "transaction_id"]

    def validate(self, attrs):
        if "status" not in attrs:
            raise serializers.ValidationError({"status": "Este campo é obrigatório."})
        return attrs

    def validate_status(self, value):
        if value == self.instance.status:
            raise serializers.ValidationError("O pagamento já possui esse status.")
        return value

    def update(self, instance, validated_data):
        try:
            return update_payment_status(
                payment=instance,
                new_status=validated_data["status"],
                actor=self.context["request"].user,
                transaction_id=validated_data.get("transaction_id", ""),
                amount_paid=validated_data.get("amount_paid"),
            )
        except OrderServiceError as exc:
            raise serializers.ValidationError({"status": str(exc)}) from exc

    def to_representation(self, instance):
        return PaymentSerializer(instance, context=self.context).data
