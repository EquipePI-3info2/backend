from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from orders.models import OrderKitComponent, OrderKitItem


class OrderKitComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderKitComponent
        fields = ["id", "product", "product_name", "quantity_per_kit"]
        read_only_fields = fields


class OrderKitItemSerializer(serializers.ModelSerializer):
    components = OrderKitComponentSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    kit_slug = serializers.CharField(source="kit.slug", read_only=True)
    kit_image = serializers.SerializerMethodField()

    class Meta:
        model = OrderKitItem
        fields = [
            "id",
            "kit",
            "kit_slug",
            "kit_name",
            "kit_image",
            "quantity",
            "unit_price",
            "subtotal",
            "components",
        ]
        read_only_fields = fields

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_kit_image(self, obj):
        if not obj.kit.image:
            return None
        request = self.context.get("request")
        url = obj.kit.image.url
        return request.build_absolute_uri(url) if request else url
