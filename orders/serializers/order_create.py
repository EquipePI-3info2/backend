from rest_framework import serializers

from catalog.models import Product
from core.models import Address
from orders.models import Order, Payment
from orders.services import OrderServiceError, create_order

from .order import OrderSerializer


class OrderItemCreateSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True, category__is_active=True)
    )
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.ModelSerializer):
    address = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.none(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    payment_method = serializers.ChoiceField(
        choices=Payment.Method.choices,
        write_only=True,
    )
    items = OrderItemCreateSerializer(
        many=True,
        write_only=True,
        allow_empty=False,
    )

    class Meta:
        model = Order
        fields = [
            "delivery_method",
            "address",
            "delivery_notes",
            "payment_method",
            "items",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            self.fields["address"].queryset = Address.objects.filter(
                user=request.user
            )

    def validate_items(self, items):
        used_products = set()
        for item in items:
            product = item["product"]
            if product.pk in used_products:
                raise serializers.ValidationError(
                    f"O produto '{product.name}' foi enviado mais de uma vez."
                )
            if product.stock < item["quantity"]:
                raise serializers.ValidationError(
                    f"Estoque insuficiente para '{product.name}'."
                )
            used_products.add(product.pk)
        return items

    def validate(self, attrs):
        method = attrs.get("delivery_method", Order.DeliveryMethod.DELIVERY)
        address = attrs.get("address")
        request = self.context["request"]

        if not Address.objects.filter(user=request.user).exists():
            raise serializers.ValidationError(
                {"address": "Cadastre ao menos um endereço antes de realizar um pedido."}
            )

        if method == Order.DeliveryMethod.DELIVERY and address is None:
            raise serializers.ValidationError(
                {"address": "Selecione um endereço para o pedido com entrega."}
            )
        if method == Order.DeliveryMethod.PICKUP and address is not None:
            raise serializers.ValidationError(
                {"address": "Não envie endereço para retirada no local."}
            )
        return attrs

    def create(self, validated_data):
        try:
            return create_order(
                user=self.context["request"].user,
                address=validated_data.pop("address", None),
                delivery_method=validated_data.get(
                    "delivery_method",
                    Order.DeliveryMethod.DELIVERY,
                ),
                delivery_notes=validated_data.get("delivery_notes", ""),
                payment_method=validated_data.pop("payment_method"),
                items=validated_data.pop("items"),
            )
        except OrderServiceError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def to_representation(self, instance):
        return OrderSerializer(instance, context=self.context).data
