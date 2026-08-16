from rest_framework import serializers

from orders.models import Order
from orders.services import OrderServiceError, transition_order_status


class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["status"]

    def validate(self, attrs):
        if "status" not in attrs:
            raise serializers.ValidationError({"status": "Este campo é obrigatório."})
        return attrs

    def validate_status(self, value):
        if value == self.instance.status:
            raise serializers.ValidationError("O pedido já possui esse status.")
        return value

    def update(self, instance, validated_data):
        try:
            return transition_order_status(
                order=instance,
                new_status=validated_data["status"],
                actor=self.context["request"].user,
            )
        except OrderServiceError as exc:
            raise serializers.ValidationError({"status": str(exc)}) from exc

    def to_representation(self, instance):
        from .order import OrderSerializer

        return OrderSerializer(instance, context=self.context).data
