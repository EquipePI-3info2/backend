from rest_framework import serializers

from orders.models import Order

from .order_item import OrderItemSerializer
from .order_kit_item import OrderKitItemSerializer
from .payment import PaymentSerializer


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    kit_items = OrderKitItemSerializer(many=True, read_only=True)
    payment = PaymentSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    delivery_method_display = serializers.CharField(
        source="get_delivery_method_display",
        read_only=True,
    )
    total_items = serializers.SerializerMethodField()
    customer_name = serializers.CharField(source="user.name", read_only=True)
    customer_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "code",
            "customer_name",
            "customer_email",
            "status",
            "status_display",
            "delivery_method",
            "delivery_method_display",
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
            "cancelled_at",
            "total_items",
            "items",
            "kit_items",
            "payment",
        ]
        read_only_fields = fields

    def get_total_items(self, obj: Order) -> int:
        prefetched = getattr(obj, "_prefetched_objects_cache", {})
        product_items = prefetched.get("items")
        kit_items = prefetched.get("kit_items")

        product_total = (
            sum(item.quantity for item in product_items)
            if product_items is not None
            else sum(item.quantity for item in obj.items.all())
        )
        kit_total = (
            sum(item.quantity for item in kit_items)
            if kit_items is not None
            else sum(item.quantity for item in obj.kit_items.all())
        )
        return product_total + kit_total
