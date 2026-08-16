from rest_framework import serializers

from ..models import Flavor


class FlavorSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Flavor
        fields = ["id", "name", "slug"]


class FlavorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flavor
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]


class FlavorWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flavor
        fields = ["name", "description", "is_active"]
