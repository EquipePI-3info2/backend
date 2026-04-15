from django.db import models


class Pedido(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('confirmado', 'Confirmado'),
        ('em_preparo', 'Em preparo'),
        ('entregue', 'Entregue'),
        ('cancelado', 'Cancelado'),
    ]

    data_pedido = models.DateTimeField(auto_now_add=True)

    status_pedido = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente'
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    desconto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    observacoes = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    usuario = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='pedidos'
    )

    pagamento = models.ForeignKey(
        'Pagamento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pedidos'
    )

    def calcular_total(self):
        subtotal = self.subtotal or 0
        desconto = self.desconto or 0
        self.total = subtotal - desconto

    def save(self, *args, **kwargs):
        self.calcular_total()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'(Pedido {self.id}) - Total: {self.total}'

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-data_pedido']
