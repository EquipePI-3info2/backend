"""
stock/models/stock_movement.py

Ajustes vs versão anterior:
  - movement_type: choices ✓ (sugestão do professor — era VARCHAR sem choices)
  - quantity: PositiveIntegerField ✓ (era VARCHAR — bug crítico corrigido)
  - Signal atualiza Product.stock automaticamente ✓

Nota sobre ADJUSTMENT:
  O tipo "adjustment" NÃO atualiza o estoque automaticamente via signal.
  Para ajuste manual, o admin deve alterar diretamente o campo Product.stock
  e registrar o motivo aqui como histórico de auditoria.
"""
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from catalog.models import Product


class StockMovement(models.Model):

    class MovementType(models.TextChoices):
        IN = "in", "Entrada (compra / reposição)"
        OUT = "out", "Saída (venda)"
        ADJUSTMENT = "adjustment", "Ajuste manual"
        LOSS = "loss", "Perda / descarte"
        RETURN = "return", "Devolução de cliente"

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="stock_movements",
        verbose_name="Produto",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
        verbose_name="Responsável",
        help_text="Usuário que registrou a movimentação.",
    )
    # CORREÇÃO professor: tipo_movimentacao VARCHAR → choices
    movement_type = models.CharField(
        "Tipo",
        max_length=20,
        choices=MovementType.choices,
    )
    # CORREÇÃO professor: quantidade VARCHAR → PositiveIntegerField
    quantity = models.PositiveIntegerField(
        "Quantidade",
        help_text="Sempre positivo. O tipo determina se entra ou sai do estoque.",
    )
    reason = models.CharField("Motivo", max_length=250, blank=True)
    created_at = models.DateTimeField("Registrado em", auto_now_add=True)

    class Meta:
        verbose_name = "Movimentação de estoque"
        verbose_name_plural = "Movimentações de estoque"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.get_movement_type_display()} | "
            f"{self.product.name} | "
            f"{self.quantity} un."
        )


# ── Signal: atualiza Product.stock automaticamente ────────────────────────────
@receiver(post_save, sender=StockMovement)
def update_product_stock(sender, instance, created, **kwargs):
    """
    Incrementa ou decrementa Product.stock após cada movimentação nova.

    Fluxo:
      IN / RETURN → soma quantidade
      OUT / LOSS  → subtrai quantidade
      ADJUSTMENT  → não altera automaticamente (requer edição direta no admin)
    """
    if not created:
        return

    product = instance.product

    if instance.movement_type in (
        StockMovement.MovementType.IN,
        StockMovement.MovementType.RETURN,
    ):
        product.stock = models.F("stock") + instance.quantity

    elif instance.movement_type in (
        StockMovement.MovementType.OUT,
        StockMovement.MovementType.LOSS,
    ):
        product.stock = models.F("stock") - instance.quantity

    else:
        # ADJUSTMENT: não altera via signal
        return

    product.save(update_fields=["stock"])
    product.refresh_from_db()
