"""
stock/models/stock_movement.py

CORREÇÕES vs modelagem original:
  - tipo_movimentacao VARCHAR(150) → choices (ENUM seguro)
  - quantidade VARCHAR(45)         → INT  ← bug crítico corrigido
  - Adicionado: created_at
  - Decrementa/incrementa estoque automaticamente via signal
"""
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from catalog.models import Product


class StockMovement(models.Model):

    class MovementType(models.TextChoices):
        IN           = "in",           "Entrada (compra/reposição)"
        OUT          = "out",          "Saída (venda)"
        ADJUSTMENT   = "adjustment",   "Ajuste manual"
        LOSS         = "loss",         "Perda / descarte"
        RETURN       = "return",       "Devolução"

    product         = models.ForeignKey(
        Product, on_delete=models.PROTECT,
        related_name="stock_movements", verbose_name="Produto"
    )
    user            = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="stock_movements", verbose_name="Responsável",
        help_text="Usuário que registrou a movimentação."
    )
    # CORREÇÃO: era VARCHAR(150) → choices
    movement_type   = models.CharField(
        "Tipo", max_length=20, choices=MovementType.choices
    )
    # CORREÇÃO: era VARCHAR(45) → INT
    quantity        = models.PositiveIntegerField(
        "Quantidade",
        help_text="Sempre positivo. O tipo determina se entra ou sai do estoque."
    )
    reason          = models.CharField("Motivo", max_length=250, blank=True)
    created_at      = models.DateTimeField("Registrado em", auto_now_add=True)

    class Meta:
        verbose_name        = "Movimentação de estoque"
        verbose_name_plural = "Movimentações de estoque"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"{self.get_movement_type_display()} | {self.product.name} | {self.quantity} un."


# ── Signal: atualiza Product.stock automaticamente ────────────────────────────
@receiver(post_save, sender=StockMovement)
def update_product_stock(sender, instance, created, **kwargs):
    """
    Atualiza o estoque do produto toda vez que uma movimentação é criada.
    Entradas (in, return) somam. Saídas (out, loss) subtraem.
    """
    if not created:
        return  # só processa movimentações novas

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
    # ADJUSTMENT: não altera automaticamente (requer ajuste manual do campo)

    product.save(update_fields=["stock"])
    product.refresh_from_db()
