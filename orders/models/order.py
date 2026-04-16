"""
orders/models/order.py

CORREÇÕES vs modelagem original:
  - status_pedido VARCHAR(45) → choices (ENUM seguro, sem valor inválido)
  - codigo_pedido VARCHAR(45) → gerado automaticamente (UUID curto, único)
  - Adicionado: endereço de entrega (obrigatório para e-commerce)
  - Adicionado: created_at, updated_at
  - pagamento: OneToOne (1 pedido → 1 pagamento)
"""
import uuid
from django.conf import settings
from django.db import models
from .payment import Payment


class Order(models.Model):

    class Status(models.TextChoices):
        PENDING    = "pending",    "Aguardando confirmação"
        CONFIRMED  = "confirmed",  "Confirmado"
        PREPARING  = "preparing",  "Em preparo"
        READY      = "ready",      "Pronto para entrega"
        DELIVERING = "delivering", "Em entrega"
        DELIVERED  = "delivered",  "Entregue"
        CANCELLED  = "cancelled",  "Cancelado"

    # ── Relações ──────────────────────────────────────────────
    user    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="Cliente",
    )
    payment = models.OneToOneField(
        Payment,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="order",
        verbose_name="Pagamento",
    )

    # ── Identificação ─────────────────────────────────────────
    code = models.CharField(
        "Código do pedido", max_length=20, unique=True, editable=False,
        help_text="Gerado automaticamente. Ex: BRK-A3F9K2.",
    )

    # ── Valores ───────────────────────────────────────────────
    subtotal = models.DecimalField("Subtotal",  max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField("Desconto",  max_digits=10, decimal_places=2, default=0)
    total    = models.DecimalField("Total",     max_digits=10, decimal_places=2, default=0)

    # ── Status ────────────────────────────────────────────────
    status = models.CharField(
        "Status", max_length=20, choices=Status.choices, default=Status.PENDING
    )

    # ── Endereço de entrega ───────────────────────────────────
    delivery_address  = models.CharField("Endereço",    max_length=300, blank=True)
    delivery_city     = models.CharField("Cidade",      max_length=100, blank=True)
    delivery_state    = models.CharField("Estado",      max_length=2,   blank=True)
    delivery_zip      = models.CharField("CEP",         max_length=9,   blank=True)
    delivery_notes    = models.TextField("Observações", blank=True)

    # ── Metadados ─────────────────────────────────────────────
    created_at = models.DateTimeField("Criado em",     auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name        = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"Pedido {self.code} — {self.user} — {self.get_status_display()}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = "BRK-" + uuid.uuid4().hex[:6].upper()
        super().save(*args, **kwargs)

    def recalculate_totals(self):
        """Recalcula subtotal e total a partir dos itens."""
        from django.db.models import Sum, F
        agg = self.items.aggregate(sub=Sum(F("quantity") * F("unit_price")))
        self.subtotal = agg["sub"] or 0
        self.total    = max(self.subtotal - self.discount, 0)
        self.save(update_fields=["subtotal", "total"])
