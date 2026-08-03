from rest_framework import serializers

from orders.models import OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_slug = serializers.CharField(source="product.slug", read_only=True)
    product_image = serializers.ImageField(source="product.image", read_only=True)
    category = serializers.CharField(source="product.category.name", read_only=True)
    flavor = serializers.CharField(
        source="product.flavor.name",
        read_only=True,
        allow_null=True,
    )
    subtotal = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "product_slug",
            "product_image",
            "category",
            "flavor",
            "quantity",
            "unit_price",
            "subtotal",
        ]
        read_only_fields = fields
