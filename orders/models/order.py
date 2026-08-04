import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.utils import timezone

from .payment import Payment


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Aguardando pagamento"
        CONFIRMED = "confirmed", "Confirmado"
        PREPARING = "preparing", "Em preparo"
        READY = "ready", "Pronto"
        DELIVERING = "delivering", "Em entrega"
        DELIVERED = "delivered", "Entregue"
        CANCELLED = "cancelled", "Cancelado"

    class DeliveryMethod(models.TextChoices):
        DELIVERY = "delivery", "Entrega"
        PICKUP = "pickup", "Retirada no local"

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
    code = models.CharField(
        "Código do pedido",
        max_length=20,
        unique=True,
        editable=False,
        help_text="Gerado automaticamente. Ex: BRK-A3F9K2.",
    )
    subtotal = models.DecimalField("Subtotal", max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField("Desconto", max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(
        "Taxa de entrega",
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Calculada pelo backend. Zero enquanto a regra de frete não estiver configurada.",
    )
    total = models.DecimalField("Total", max_digits=10, decimal_places=2, default=0)
    status = models.CharField(
        "Status",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    delivery_method = models.CharField(
        "Forma de recebimento",
        max_length=20,
        choices=DeliveryMethod.choices,
        default=DeliveryMethod.DELIVERY,
    )

    # Snapshot do endereço utilizado no pedido. Ele não muda caso o usuário edite
    # ou exclua o endereço cadastrado depois da compra.
    delivery_address = models.CharField("Logradouro", max_length=300, blank=True)
    delivery_city = models.CharField("Cidade", max_length=100, blank=True)
    delivery_state = models.CharField("Estado (UF)", max_length=2, blank=True)
    delivery_zip = models.CharField("CEP", max_length=9, blank=True)
    delivery_notes = models.TextField("Observações", blank=True)

    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)
    confirmed_at = models.DateTimeField("Confirmado em", null=True, blank=True)
    delivered_at = models.DateTimeField("Entregue em", null=True, blank=True)
    cancelled_at = models.DateTimeField("Cancelado em", null=True, blank=True)
    stock_deducted_at = models.DateTimeField(
        "Estoque baixado em",
        null=True,
        blank=True,
        editable=False,
    )
    stock_returned_at = models.DateTimeField(
        "Estoque devolvido em",
        null=True,
        blank=True,
        editable=False,
    )

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(subtotal__gte=0),
                name="order_subtotal_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(discount__gte=0),
                name="order_discount_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(delivery_fee__gte=0),
                name="order_delivery_fee_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(total__gte=0),
                name="order_total_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(discount__lte=F("subtotal")),
                name="order_discount_not_greater_than_subtotal",
            ),
        ]

    def __str__(self):
        return f"{self.code} - {self.user.name}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = f"BRK-{uuid.uuid4().hex[:6].upper()}"

        self.total = max(
            self.subtotal - self.discount + self.delivery_fee,
            Decimal("0.00"),
        )
        super().save(*args, **kwargs)

    def recalculate_totals(self):
        subtotal = self.items.aggregate(
            subtotal=Sum(
                ExpressionWrapper(
                    F("quantity") * F("unit_price"),
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                )
            )
        )["subtotal"] or Decimal("0.00")

        self.subtotal = subtotal
        self.total = max(
            self.subtotal - self.discount + self.delivery_fee,
            Decimal("0.00"),
        )
        self.save(update_fields=["subtotal", "total", "updated_at"])

    def mark_confirmed(self):
        if self.confirmed_at is None:
            self.confirmed_at = timezone.now()

    def mark_delivered(self):
        if self.delivered_at is None:
            self.delivered_at = timezone.now()

    def mark_cancelled(self):
        if self.cancelled_at is None:
            self.cancelled_at = timezone.now()