"""
orders/models/order_item.py

Sem alterações em relação à versão revisada — já estava correto:
  - quantity: PositiveIntegerField ✓
  - unit_price: snapshot do preço no momento da compra ✓
  - subtotal: property calculada (sem redundância) ✓
  - unique_together [order, product]: evita duplicatas ✓
"""
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
    quantity = models.PositiveIntegerField("Quantidade", default=1)
    # Snapshot do preço: não muda se o produto mudar de preço depois
    unit_price = models.DecimalField(
        "Preço unitário",
        max_digits=8,
        decimal_places=2,
        help_text="Salvo no momento da compra. Não sofre alterações retroativas.",
    )

    class Meta:
        verbose_name        = "Item do pedido"
        verbose_name_plural = "Itens do pedido"
        unique_together     = [["order", "product"]]

    def __str__(self):
        return f"{self.quantity}x {self.product.name} (Pedido {self.order.code})"

    @property
    def subtotal(self):
        """Subtotal calculado: quantity × unit_price."""
        return self.quantity * self.unit_price
