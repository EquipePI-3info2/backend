from django.db import models


class Pagamento(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('recusado', 'Recusado'),
    ]

    METODO_CHOICES = [
        ('pix', 'Pix'),
        ('cartao', 'Cartão'),
        ('dinheiro', 'Dinheiro'),
    ]

    TIPO_MOVIMENTACAO_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
    ]

    valor = models.DecimalField(max_digits=10, decimal_places=2)

    status_pagamento = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente'
    )

    metodo_pagamento = models.CharField(max_length=20, choices=METODO_CHOICES)
    tipo_movimentacao = models.CharField(max_length=20, choices=TIPO_MOVIMENTACAO_CHOICES)

    def __str__(self):
        return f'(Pagamento {self.id}) {self.valor}'

    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
