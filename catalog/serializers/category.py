from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from ..models import Category


class CategorySerializer(serializers.ModelSerializer):
    """Serializer público — usado na vitrine e na Home."""
    image_url = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id", "name", "slug", "description",
            "image_url", "is_active", "order",
            "product_count", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_image_url(self, obj) -> str | None:
        if not obj.image:
            return None
        request = self.context.get("request")
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url

    @extend_schema_field(serializers.IntegerField())
    def get_product_count(self, obj) -> int:
        # Usa o count do prefetch quando disponível
        if hasattr(obj, "_prefetched_objects_cache"):
            return len(obj._prefetched_objects_cache.get("products", []))
        return obj.products.filter(is_active=True).count()


class CategoryWriteSerializer(serializers.ModelSerializer):
    """Serializer de escrita — somente para admin."""
    class Meta:
        model = Category
        fields = ["name", "description", "image", "is_active", "order"]
