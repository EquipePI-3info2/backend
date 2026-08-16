from collections import defaultdict

from rest_framework import serializers

from catalog.models import Kit, Product
from core.models import Address
from orders.models import Order, Payment
from orders.services import OrderServiceError, create_order

from .order import OrderSerializer


class OrderItemCreateSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True, category__is_active=True)
    )
    quantity = serializers.IntegerField(min_value=1)


class OrderKitCreateSerializer(serializers.Serializer):
    kit = serializers.PrimaryKeyRelatedField(queryset=Kit.objects.filter(is_active=True))
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
        required=False,
        allow_empty=True,
    )
    kits = OrderKitCreateSerializer(
        many=True,
        write_only=True,
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = Order
        fields = [
            "delivery_method",
            "address",
            "delivery_notes",
            "payment_method",
            "items",
            "kits",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            self.fields["address"].queryset = Address.objects.filter(user=request.user)

    def validate_items(self, items):
        used_products = set()
        for item in items:
            product = item["product"]
            if product.pk in used_products:
                raise serializers.ValidationError(
                    f"O produto '{product.name}' foi enviado mais de uma vez."
                )
            used_products.add(product.pk)
        return items

    def validate_kits(self, kits):
        used_kits = set()
        for item in kits:
            kit = item["kit"]
            if kit.pk in used_kits:
                raise serializers.ValidationError(
                    f"O kit '{kit.name}' foi enviado mais de uma vez."
                )
            used_kits.add(kit.pk)
        return kits

    def _validate_combined_stock(self, items, kits):
        required = defaultdict(int)
        products = {}

        for item in items:
            product = item["product"]
            products[product.pk] = product
            required[product.pk] += item["quantity"]

        for requested_kit in kits:
            kit = requested_kit["kit"]
            kit_items = list(
                kit.items.select_related("product", "product__category").all()
            )
            if not kit_items:
                raise serializers.ValidationError(
                    {"kits": f"O kit '{kit.name}' não possui produtos cadastrados."}
                )

            for kit_item in kit_items:
                product = kit_item.product
                if not product.is_active or not product.category.is_active:
                    raise serializers.ValidationError(
                        {
                            "kits": (
                                f"O kit '{kit.name}' contém o produto indisponível "
                                f"'{product.name}'."
                            )
                        }
                    )
                products[product.pk] = product
                required[product.pk] += (
                    kit_item.quantity * requested_kit["quantity"]
                )

        for product_id, quantity in required.items():
            product = products[product_id]
            if product.stock < quantity:
                raise serializers.ValidationError(
                    {
                        "items": (
                            f"Estoque insuficiente para '{product.name}'. "
                            f"Necessário: {quantity}; disponível: {product.stock}."
                        )
                    }
                )

    def validate(self, attrs):
        method = attrs.get("delivery_method", Order.DeliveryMethod.DELIVERY)
        address = attrs.get("address")
        request = self.context["request"]
        items = attrs.get("items", [])
        kits = attrs.get("kits", [])

        if not items and not kits:
            raise serializers.ValidationError(
                {"items": "Adicione ao menos um produto ou kit ao pedido."}
            )

        self._validate_combined_stock(items, kits)

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
                items=validated_data.pop("items", []),
                kits=validated_data.pop("kits", []),
            )
        except OrderServiceError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def to_representation(self, instance):
        return OrderSerializer(instance, context=self.context).data
