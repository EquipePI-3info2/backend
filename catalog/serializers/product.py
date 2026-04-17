# catalog/serializers/product.py

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from ..models import Flavor, Product
from .category import CategorySerializer


# ── FlavorSerializer (somente leitura, embutido no produto) ───────────────────
class FlavorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flavor
        fields = ["id", "name", "slug"]


# ── Serializer público (vitrine) ──────────────────────────────────────────────
class ProductSerializer(serializers.ModelSerializer):
    """
    Retornado para qualquer usuário (inclusive anônimo).
    NÃO expõe cost_price nem margens.
    """
    category = CategorySerializer(read_only=True)
    flavor = FlavorSerializer(read_only=True)        # ← objeto, não ID
    image_url = serializers.SerializerMethodField()
    is_in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "description",
            "flavor",                                     # ← {id, name, slug}
            "category", "price",
            "image_url", "is_in_stock", "stock",
            "is_active", "is_featured",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_image_url(self, obj) -> str | None:
        if not obj.image:
            return None
        request = self.context.get("request")
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url


# ── Serializer admin (painel de controle) ─────────────────────────────────────
class ProductAdminSerializer(serializers.ModelSerializer):
    """
    Retornado somente para is_staff=True.
    Inclui cost_price, margens e campos de escrita.
    """
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_slug = serializers.CharField(source="category.slug", read_only=True)
    flavor = FlavorSerializer(read_only=True)   # ← objeto, não ID
    image_url = serializers.SerializerMethodField()
    is_in_stock = serializers.BooleanField(read_only=True)
    gross_margin_pct = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    gross_profit = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "description",
            "flavor",                                     # ← {id, name, slug}
            "category", "category_name", "category_slug",
            "price", "cost_price",
            "gross_margin_pct", "gross_profit",
            "image", "image_url",
            "stock", "is_in_stock",
            "is_active", "is_featured",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_image_url(self, obj) -> str | None:
        if not obj.image:
            return None
        request = self.context.get("request")
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url


# ── Serializer de escrita (POST / PATCH) ──────────────────────────────────────
class ProductWriteSerializer(serializers.ModelSerializer):
    """
    Usado pelo admin para criar e editar produtos.
    flavor e category recebem PKs inteiras (padrão de escrita do DRF).
    """
    class Meta:
        model = Product
        fields = [
            "name", "description",
            "flavor",              # ← aceita ID inteiro (PK) na escrita
            "category", "price", "cost_price",
            "image", "stock", "is_active", "is_featured",
        ]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("O preço de venda deve ser maior que zero.")
        return value

    def validate_cost_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("O preço de custo não pode ser negativo.")
        return value

    def validate(self, attrs):
        price = attrs.get("price")
        cost_price = attrs.get("cost_price")
        if price and cost_price and cost_price >= price:
            raise serializers.ValidationError(
                {"cost_price": "O preço de custo deve ser menor que o preço de venda."}
            )
        return attrs
