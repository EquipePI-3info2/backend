from rest_framework import serializers

from orders.models import Order


class OrderUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Order

        fields = [
            "status",
        ]
