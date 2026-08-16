from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Payment(models.Model):
    """Pagamento ativo do pedido no MVP.

    O relacionamento atual é um para um: cada pedido possui um pagamento ativo.
    Quando o fluxo do Mercado Pago for implementado, novas tentativas podem ser
    modeladas em uma tabela específica de transações sem alterar o histórico do pedido.
    """

    class Method(models.TextChoices):
        PIX = "pix", "Pix"
        CREDIT_CARD = "credit_card", "Cartão de crédito"
        DEBIT_CARD = "debit_card", "Cartão de débito"
        CASH = "cash", "Dinheiro"
        BANK_SLIP = "bank_slip", "Boleto"

    class Status(models.TextChoices):
        PENDING = "pending", "Aguardando pagamento"
        APPROVED = "approved", "Aprovado"
        REFUSED = "refused", "Recusado"
        REFUNDED = "refunded", "Estornado"
        CANCELLED = "cancelled", "Cancelado"

    method = models.CharField("Método", max_length=20, choices=Method.choices)
    status = models.CharField(
        "Status",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    amount_paid = models.DecimalField(
        "Valor pago",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    transaction_id = models.CharField(
        "ID da transação",
        max_length=200,
        blank=True,
        help_text="ID retornado pelo gateway de pagamento.",
    )
    paid_at = models.DateTimeField("Pago em", null=True, blank=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount_paid__gte=0),
                name="payment_amount_paid_non_negative",
            )
        ]

    def __str__(self):
        return (
            f"{self.get_method_display()} — "
            f"{self.get_status_display()} — "
            f"R$ {self.amount_paid}"
        )
