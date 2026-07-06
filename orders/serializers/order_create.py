from django.db import transaction
from django.db.models import F
from rest_framework import serializers

from catalog.models import Product
from orders.models import Order, OrderItem


class OrderItemCreateSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True)
    )

    quantity = serializers.IntegerField(
        min_value=1
    )


class OrderCreateSerializer(serializers.ModelSerializer):

    items = OrderItemCreateSerializer(
        many=True,
        write_only=True,
        allow_empty=False,
    )

    class Meta:
        model = Order
        fields = [
            "delivery_address",
            "delivery_city",
            "delivery_state",
            "delivery_zip",
            "delivery_notes",
            "delivery_fee",
            "discount",
            "items",
        ]

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError(
                "O pedido deve possuir pelo menos um item."
            )

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

    @transaction.atomic
    def create(self, validated_data):

        items = validated_data.pop("items")

        order = Order.objects.create(
            user=self.context["request"].user,
            **validated_data,
        )

        order_items = []

        for item in items:

            product = item["product"]

            order_items.append(
                OrderItem(
                    order=order,
                    product=product,
                    quantity=item["quantity"],
                    unit_price=product.price,
                )
            )

            Product.objects.filter(
                pk=product.pk
            ).update(
                stock=F("stock") - item["quantity"]
            )

        OrderItem.objects.bulk_create(order_items)

        order.recalculate_totals()

        return order
