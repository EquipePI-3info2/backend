from django.core.validators import MinValueValidator
from django.db import models

from catalog.models import Kit, Product

from .order import Order


class OrderKitItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="kit_items",
        verbose_name="Pedido",
    )
    kit = models.ForeignKey(
        Kit,
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name="Kit",
    )
    kit_name = models.CharField("Nome do kit", max_length=150)
    quantity = models.PositiveIntegerField(
        "Quantidade",
        default=1,
        validators=[MinValueValidator(1)],
    )
    unit_price = models.DecimalField(
        "Preço unitário",
        max_digits=8,
        decimal_places=2,
        help_text="Preço promocional salvo no momento da compra.",
    )

    class Meta:
        verbose_name = "Kit do pedido"
        verbose_name_plural = "Kits do pedido"
        constraints = [
            models.UniqueConstraint(
                fields=["order", "kit"],
                name="unique_kit_per_order",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="order_kit_item_quantity_greater_than_zero",
            ),
        ]

    def __str__(self):
        return f"{self.quantity}x {self.kit_name} (Pedido {self.order.code})"

    @property
    def subtotal(self):
        return self.quantity * self.unit_price


class OrderKitComponent(models.Model):
    order_kit_item = models.ForeignKey(
        OrderKitItem,
        on_delete=models.CASCADE,
        related_name="components",
        verbose_name="Kit do pedido",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_kit_components",
        verbose_name="Produto",
    )
    product_name = models.CharField("Nome do produto", max_length=150)
    quantity_per_kit = models.PositiveIntegerField(
        "Quantidade por kit",
        validators=[MinValueValidator(1)],
    )

    class Meta:
        verbose_name = "Componente do kit no pedido"
        verbose_name_plural = "Componentes dos kits nos pedidos"
        constraints = [
            models.UniqueConstraint(
                fields=["order_kit_item", "product"],
                name="unique_product_per_order_kit",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity_per_kit__gt=0),
                name="order_kit_component_quantity_greater_than_zero",
            ),
        ]

    def __str__(self):
        return f"{self.quantity_per_kit}x {self.product_name}"
