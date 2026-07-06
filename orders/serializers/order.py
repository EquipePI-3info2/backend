from rest_framework import serializers

from orders.models import Order

from .order_item import OrderItemSerializer


class OrderSerializer(serializers.ModelSerializer):

    items = OrderItemSerializer(
        many=True,
        read_only=True,
    )

    status_display = serializers.SerializerMethodField()

    total_items = serializers.SerializerMethodField()

    class Meta:
        model = Order

        fields = [
            "id",
            "code",
            "status",
            "status_display",
            "subtotal",
            "discount",
            "delivery_fee",
            "total",
            "delivery_address",
            "delivery_city",
            "delivery_state",
            "delivery_zip",
            "delivery_notes",
            "created_at",
            "updated_at",
            "confirmed_at",
            "delivered_at",
            "total_items",
            "items",
        ]

        read_only_fields = fields

    def get_status_display(self, obj):
        return obj.get_status_display()

    def get_total_items(self, obj):
        return sum(item.quantity for item in obj.items.all())
