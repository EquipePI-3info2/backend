"""
orders/models/order_item.py

CORREÇÕES vs modelagem original:
  - quantidade VARCHAR(45) → quantity INT  ← bug crítico corrigido
  - subtotal_item → calculado via property (sem redundância)
  - preco_unitario salvo no momento da compra (histórico de preço)
"""
from django.db import models
from catalog.models import Product
from .order import Order


class OrderItem(models.Model):
    order      = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        related_name="items", verbose_name="Pedido"
    )
    product    = models.ForeignKey(
        Product, on_delete=models.PROTECT,
        related_name="order_items", verbose_name="Produto"
    )
    # CORREÇÃO: era VARCHAR(45) → INT
    quantity   = models.PositiveIntegerField("Quantidade", default=1)
    # Preço no momento da compra (não muda se o produto mudar de preço)
    unit_price = models.DecimalField(
        "Preço unitário", max_digits=8, decimal_places=2,
        help_text="Salvo no momento da compra. Não muda retroativamente."
    )

    class Meta:
        verbose_name        = "Item do pedido"
        verbose_name_plural = "Itens do pedido"
        unique_together     = [["order", "product"]]

    def __str__(self):
        return f"{self.quantity}x {self.product.name} (Pedido {self.order.code})"

    @property
    def subtotal(self):
        """Subtotal do item: quantity × unit_price"""
        return self.quantity * self.unit_price
