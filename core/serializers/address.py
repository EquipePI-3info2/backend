import re

from django.db import transaction
from rest_framework import serializers

from core.models import Address


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id",
            "label",
            "street",
            "number",
            "complement",
            "neighborhood",
            "city",
            "state",
            "zip_code",
            "is_default",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_state(self, value):
        state = value.strip().upper()
        if len(state) != 2 or not state.isalpha():
            raise serializers.ValidationError("Informe a UF com duas letras.")
        return state

    def validate_zip_code(self, value):
        digits = re.sub(r"\D", "", value)
        if len(digits) != 8:
            raise serializers.ValidationError("Informe um CEP válido com oito dígitos.")
        return f"{digits[:5]}-{digits[5:]}"

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user
        has_addresses = Address.objects.filter(user=user).exists()
        make_default = validated_data.get("is_default", False) or not has_addresses

        if make_default:
            Address.objects.filter(user=user, is_default=True).update(is_default=False)

        validated_data["is_default"] = make_default
        return Address.objects.create(user=user, **validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        make_default = validated_data.get("is_default") is True
        if make_default:
            Address.objects.filter(
                user=instance.user,
                is_default=True,
            ).exclude(pk=instance.pk).update(is_default=False)

        instance = super().update(instance, validated_data)

        if not Address.objects.filter(user=instance.user, is_default=True).exists():
            instance.is_default = True
            instance.save(update_fields=["is_default", "updated_at"])

        return instance
