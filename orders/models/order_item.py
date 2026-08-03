from django.core.validators import MinValueValidator
from django.db import models

from catalog.models import Product

from .order import Order


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Pedido",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name="Produto",
    )
    quantity = models.PositiveIntegerField(
        "Quantidade",
        default=1,
        validators=[MinValueValidator(1)],
    )
    unit_price = models.DecimalField(
        "Preço unitário",
        max_digits=8,
        decimal_places=2,
        help_text="Salvo no momento da compra. Não sofre alterações retroativas.",
    )

    class Meta:
        verbose_name = "Item do pedido"
        verbose_name_plural = "Itens do pedido"
        constraints = [
            models.UniqueConstraint(
                fields=["order", "product"],
                name="unique_product_per_order",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="order_item_quantity_greater_than_zero",
            ),
        ]

    def __str__(self):
        return f"{self.quantity}x {self.product.name} (Pedido {self.order.code})"

    @property
    def subtotal(self):
        return self.quantity * self.unit_price
