from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import F

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
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="stock_movements",
        null=True,
        blank=True,
        verbose_name="Pedido",
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
    movement_type = models.CharField(
        "Tipo",
        max_length=20,
        choices=MovementType.choices,
    )
    quantity = models.PositiveIntegerField(
        "Quantidade",
        validators=[MinValueValidator(1)],
        help_text="Sempre positivo. O tipo determina se entra ou sai do estoque.",
    )
    reason = models.CharField("Motivo", max_length=250, blank=True)
    created_at = models.DateTimeField("Registrado em", auto_now_add=True)

    class Meta:
        verbose_name = "Movimentação de estoque"
        verbose_name_plural = "Movimentações de estoque"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="stock_movement_quantity_greater_than_zero",
            )
        ]

    def __str__(self):
        return (
            f"{self.get_movement_type_display()} | "
            f"{self.product.name} | "
            f"{self.quantity} un."
        )

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Movimentações de estoque não podem ser alteradas.")

        with transaction.atomic():
            product = Product.objects.select_for_update().get(pk=self.product_id)

            if self.movement_type in {
                self.MovementType.OUT,
                self.MovementType.LOSS,
            } and product.stock < self.quantity:
                raise ValidationError(
                    {"quantity": f"Estoque insuficiente para '{product.name}'."}
                )

            super().save(*args, **kwargs)

            if self.movement_type in {
                self.MovementType.IN,
                self.MovementType.RETURN,
            }:
                Product.objects.filter(pk=product.pk).update(
                    stock=F("stock") + self.quantity
                )
            elif self.movement_type in {
                self.MovementType.OUT,
                self.MovementType.LOSS,
            }:
                Product.objects.filter(pk=product.pk).update(
                    stock=F("stock") - self.quantity
                )
