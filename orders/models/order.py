import uuid

from django.conf import settings
from django.db import models
from django.db.models import DecimalField
from django.db.models import ExpressionWrapper
from django.db.models import F
from django.db.models import Sum
from django.utils import timezone

from .payment import Payment


class Order(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Aguardando confirmação"
        CONFIRMED = "confirmed", "Confirmado"
        PREPARING = "preparing", "Em preparo"
        READY = "ready", "Pronto para entrega"
        DELIVERING = "delivering", "Em entrega"
        DELIVERED = "delivered", "Entregue"
        CANCELLED = "cancelled", "Cancelado"

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

    subtotal = models.DecimalField(
        "Subtotal",
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    discount = models.DecimalField(
        "Desconto",
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    delivery_fee = models.DecimalField(
        "Taxa de entrega",
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Frete ou retirada.",
    )

    total = models.DecimalField(
        "Total",
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    status = models.CharField(
        "Status",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    delivery_address = models.CharField(
        "Logradouro",
        max_length=300,
        blank=True,
    )

    delivery_city = models.CharField(
        "Cidade",
        max_length=100,
        blank=True,
    )

    delivery_state = models.CharField(
        "Estado",
        max_length=2,
        blank=True,
    )

    delivery_zip = models.CharField(
        "CEP",
        max_length=9,
        blank=True,
    )

    delivery_notes = models.TextField(
        "Observações",
        blank=True,
    )

    created_at = models.DateTimeField(
        "Criado em",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        "Atualizado em",
        auto_now=True,
    )

    confirmed_at = models.DateTimeField(
        "Confirmado em",
        null=True,
        blank=True,
    )

    delivered_at = models.DateTimeField(
        "Entregue em",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} - {self.user.name}"

    def save(self, *args, **kwargs):

        if not self.code:
            self.code = f"BRK-{uuid.uuid4().hex[:6].upper()}"

        self.total = max(
            self.subtotal - self.discount + self.delivery_fee,
            0,
        )

        if (
            self.status == self.Status.CONFIRMED
            and self.confirmed_at is None
        ):
            self.confirmed_at = timezone.now()

        if (
            self.status == self.Status.DELIVERED
            and self.delivered_at is None
        ):
            self.delivered_at = timezone.now()

        super().save(*args, **kwargs)

    def recalculate_totals(self):
        """
        Recalcula subtotal e total a partir dos itens.
        """

        subtotal = self.items.aggregate(
            subtotal=Sum(
                ExpressionWrapper(
                    F("quantity") * F("unit_price"),
                    output_field=DecimalField(
                        max_digits=10,
                        decimal_places=2,
                    ),
                )
            )
        )["subtotal"] or 0

        self.subtotal = subtotal

        self.total = max(
            self.subtotal - self.discount + self.delivery_fee,
            0,
        )

        self.save(
            update_fields=[
                "subtotal",
                "total",
                "confirmed_at",
                "delivered_at",
                "updated_at",
            ]
        )
