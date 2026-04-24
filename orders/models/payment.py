"""
orders/models/payment.py

Por que Payment é uma tabela separada e não campos no Pedido?
─────────────────────────────────────────────────────────────
O professor levantou: "pra que serve a tabela pagamento? daria para unir."
Optamos por manter separado pelos seguintes motivos:

  1. Separação de responsabilidades: pedido = intenção de compra;
     pagamento = transação financeira. São ciclos de vida distintos.

  2. Múltiplas tentativas: um pedido pode ter várias tentativas de pagamento
     antes de ser aprovado (ex: cartão recusado → nova tentativa via Pix).
     Com Payment separado, basta criar um novo Payment sem alterar o Order.

  3. Integração com gateway: campos como transaction_id e paid_at são
     exclusivos do Payment e não fazem sentido no Pedido.

  4. Relatórios financeiros: consultas de receita, estorno e inadimplência
     ficam mais simples sem misturar com dados do pedido.

Relação: Order → OneToOne → Payment (1 pagamento ativo por pedido).

Sugestão do professor atendida nos choices:
  - status_pagamento: choices ✓  (era VARCHAR sem choices)
  - método pagamento: choices ✓  (era VARCHAR sem choices)
"""
from django.db import models


class Payment(models.Model):

    class Method(models.TextChoices):
        PIX         = "pix",         "Pix"
        CREDIT_CARD = "credit_card", "Cartão de Crédito"
        DEBIT_CARD  = "debit_card",  "Cartão de Débito"
        CASH        = "cash",        "Dinheiro"
        BANK_SLIP   = "bank_slip",   "Boleto"

    class Status(models.TextChoices):
        PENDING   = "pending",   "Aguardando pagamento"
        APPROVED  = "approved",  "Aprovado"
        REFUSED   = "refused",   "Recusado"
        REFUNDED  = "refunded",  "Estornado"
        CANCELLED = "cancelled", "Cancelado"

    method = models.CharField(
        "Método",
        max_length=20,
        choices=Method.choices,
        # CORREÇÃO: era VARCHAR(45) sem choices
    )
    status = models.CharField(
        "Status",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        # CORREÇÃO: era VARCHAR(45) sem choices
    )
    amount_paid = models.DecimalField(
        "Valor pago",
        max_digits=10,
        decimal_places=2,
    )
    transaction_id = models.CharField(
        "ID da transação",
        max_length=200,
        blank=True,
        help_text="ID retornado pelo gateway (ex: Pix txid, Stripe charge_id).",
    )
    paid_at    = models.DateTimeField("Pago em",        null=True, blank=True)
    created_at = models.DateTimeField("Criado em",      auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em",  auto_now=True)

    class Meta:
        verbose_name        = "Pagamento"
        verbose_name_plural = "Pagamentos"
        ordering            = ["-created_at"]

    def __str__(self):
        return (
            f"{self.get_method_display()} — "
            f"{self.get_status_display()} — "
            f"R$ {self.amount_paid}"
        )
