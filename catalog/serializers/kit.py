import json
from decimal import Decimal

from django.db import transaction
from django.utils.text import slugify
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from ..models import Kit, KitItem, Product


class KitProductSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "slug", "price", "stock", "image_url"]
        read_only_fields = fields

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url


class KitItemSerializer(serializers.ModelSerializer):
    product = KitProductSerializer(read_only=True)

    class Meta:
        model = KitItem
        fields = ["id", "product", "quantity"]
        read_only_fields = fields


class KitSerializer(serializers.ModelSerializer):
    items = KitItemSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    regular_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    savings = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    available_stock = serializers.IntegerField(read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Kit
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "promotional_price",
            "regular_price",
            "savings",
            "image_url",
            "available_stock",
            "is_in_stock",
            "is_active",
            "is_featured",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url


class KitAdminSerializer(KitSerializer):
    image = serializers.ImageField(read_only=True)

    class Meta(KitSerializer.Meta):
        fields = KitSerializer.Meta.fields + ["image"]


class KitItemWriteSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField(min_value=1)


class KitWriteSerializer(serializers.ModelSerializer):
    items = KitItemWriteSerializer(many=True, required=False, write_only=True)
    items_json = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = Kit
        fields = [
            "name",
            "description",
            "promotional_price",
            "image",
            "is_active",
            "is_featured",
            "items",
            "items_json",
        ]

    def validate_name(self, value):
        slug = slugify(value)
        queryset = Kit.objects.filter(slug=slug)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                "Já existe um kit com este nome ou com um nome equivalente."
            )
        return value

    def _parse_items_json(self, value):
        if value in (None, ""):
            return None
        try:
            raw_items = json.loads(value)
        except (TypeError, ValueError) as exc:
            raise serializers.ValidationError(
                {"items_json": "A lista de produtos do kit é inválida."}
            ) from exc

        serializer = KitItemWriteSerializer(data=raw_items, many=True)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def validate(self, attrs):
        parsed_items = self._parse_items_json(attrs.pop("items_json", None))
        items = parsed_items if parsed_items is not None else attrs.get("items")

        if items is None and self.instance is not None:
            items = [
                {"product": item.product, "quantity": item.quantity}
                for item in self.instance.items.select_related("product").all()
            ]

        if not items:
            raise serializers.ValidationError(
                {"items": "Selecione ao menos um produto para compor o kit."}
            )

        used_products = set()
        regular_price = Decimal("0.00")
        for item in items:
            product = item["product"]
            if product.pk in used_products:
                raise serializers.ValidationError(
                    {"items": f"O produto '{product.name}' foi selecionado mais de uma vez."}
                )
            if not product.is_active or not product.category.is_active:
                raise serializers.ValidationError(
                    {"items": f"O produto '{product.name}' não está ativo na vitrine."}
                )
            used_products.add(product.pk)
            regular_price += product.price * item["quantity"]

        promotional_price = attrs.get(
            "promotional_price",
            getattr(self.instance, "promotional_price", None),
        )
        if promotional_price is None or promotional_price <= 0:
            raise serializers.ValidationError(
                {"promotional_price": "O preço promocional deve ser maior que zero."}
            )
        if promotional_price >= regular_price:
            raise serializers.ValidationError(
                {
                    "promotional_price": (
                        f"O preço promocional deve ser menor que o valor normal do kit "
                        f"(R$ {regular_price:.2f})."
                    )
                }
            )

        attrs["items"] = items
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop("items")
        kit = Kit.objects.create(**validated_data)
        KitItem.objects.bulk_create(
            KitItem(kit=kit, product=item["product"], quantity=item["quantity"])
            for item in items
        )
        return kit

    @transaction.atomic
    def update(self, instance, validated_data):
        items = validated_data.pop("items", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        if items is not None:
            instance.items.all().delete()
            KitItem.objects.bulk_create(
                KitItem(
                    kit=instance,
                    product=item["product"],
                    quantity=item["quantity"],
                )
                for item in items
            )
        return instance
