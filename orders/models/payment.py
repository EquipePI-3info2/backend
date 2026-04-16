"""
orders/models/payment.py

CORREÇÕES vs modelagem original:
  - metodo_pagamento VARCHAR(45) → choices (ENUM seguro)
  - status_pagamento VARCHAR(45) → choices
  - Adicionado: created_at, updated_at
"""
from django.db import models


class Payment(models.Model):

    class Method(models.TextChoices):
        PIX          = "pix",          "Pix"
        CREDIT_CARD  = "credit_card",  "Cartão de Crédito"
        DEBIT_CARD   = "debit_card",   "Cartão de Débito"
        CASH         = "cash",         "Dinheiro"
        BANK_SLIP    = "bank_slip",    "Boleto"

    class Status(models.TextChoices):
        PENDING   = "pending",   "Aguardando pagamento"
        APPROVED  = "approved",  "Aprovado"
        REFUSED   = "refused",   "Recusado"
        REFUNDED  = "refunded",  "Estornado"
        CANCELLED = "cancelled", "Cancelado"

    method          = models.CharField("Método", max_length=20, choices=Method.choices)
    status          = models.CharField(
        "Status", max_length=20, choices=Status.choices, default=Status.PENDING
    )
    amount_paid     = models.DecimalField("Valor pago", max_digits=10, decimal_places=2)
    transaction_id  = models.CharField(
        "ID da transação", max_length=200, blank=True,
        help_text="ID retornado pelo gateway de pagamento (ex: Pix txid)."
    )
    paid_at         = models.DateTimeField("Pago em", null=True, blank=True)
    created_at      = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at      = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name        = "Pagamento"
        verbose_name_plural = "Pagamentos"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"{self.get_method_display()} — {self.get_status_display()} — R$ {self.amount_paid}"
