"""
orders/models/order.py

Ajustes vs versão anterior:
  - codigo_pedido → code (gerado como BRK-XXXXXX via UUID) ✓ já implementado
  - status como TextChoices ✓ já implementado
  - Adicionado: delivery_fee (taxa de entrega) — faltava no cálculo do total
  - recalculate_totals() inclui delivery_fee no total
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
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="Cliente",
    )
    payment = models.OneToOneField(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order",
        verbose_name="Pagamento",
    )

    # ── Identificação ─────────────────────────────────────────
    code = models.CharField(
        "Código do pedido",
        max_length=20,
        unique=True,
        editable=False,
        help_text="Gerado automaticamente. Ex: BRK-A3F9K2.",
    )

    # ── Valores ───────────────────────────────────────────────
    subtotal     = models.DecimalField("Subtotal",         max_digits=10, decimal_places=2, default=0)
    discount     = models.DecimalField("Desconto",         max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(
        "Taxa de entrega",
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Frete ou taxa de entrega. 0 para retirada no local.",
    )
    total = models.DecimalField("Total", max_digits=10, decimal_places=2, default=0)

    # ── Status ────────────────────────────────────────────────
    status = models.CharField(
        "Status",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    # ── Endereço de entrega (desnormalizado) ──────────────────
    # Desnormalizado intencionalmente: garante que o endereço histórico
    # do pedido não muda se o cliente editar o endereço cadastrado.
    delivery_address = models.CharField("Logradouro",    max_length=300, blank=True)
    delivery_city    = models.CharField("Cidade",        max_length=100, blank=True)
    delivery_state   = models.CharField("Estado (UF)",   max_length=2,   blank=True)
    delivery_zip     = models.CharField("CEP",           max_length=9,   blank=True)
    delivery_notes   = models.TextField("Observações",                   blank=True)

    # ── Timestamps ────────────────────────────────────────────
    created_at   = models.DateTimeField("Criado em",     auto_now_add=True)
    updated_at   = models.DateTimeField("Atualizado em", auto_now=True)
    confirmed_at = models.DateTimeField("Confirmado em", null=True, blank=True)
    delivered_at = models.DateTimeField("Entregue em",   null=True, blank=True)

    class Meta:
        verbose_name        = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"Pedido {self.code} — {self.user} — {self.get_status_display()}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = "BRK-" + uuid.uuid4().hex[:6].upper()
        # Garante que total nunca fica inconsistente ao salvar diretamente
        self.total = max(self.subtotal - self.discount + self.delivery_fee, 0)
        super().save(*args, **kwargs)

    def recalculate_totals(self):
        """
        Recalcula subtotal e total a partir dos itens do pedido.
        Deve ser chamado após adicionar/remover/alterar itens.
        """
        from django.db.models import F, Sum
        agg = self.items.aggregate(sub=Sum(F("quantity") * F("unit_price")))
        self.subtotal = agg["sub"] or 0
        self.total    = max(self.subtotal - self.discount + self.delivery_fee, 0)
        self.save(update_fields=["subtotal", "total"])
