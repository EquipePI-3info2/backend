from decimal import Decimal

import django.core.validators
from django.db import migrations, models
from django.db.models import F, Q


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0003_alter_order_delivery_fee_alter_order_delivery_state"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="cancelled_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Cancelado em"),
        ),
        migrations.AddField(
            model_name="order",
            name="delivery_method",
            field=models.CharField(
                choices=[("delivery", "Entrega"), ("pickup", "Retirada no local")],
                default="delivery",
                max_length=20,
                verbose_name="Forma de recebimento",
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="stock_deducted_at",
            field=models.DateTimeField(blank=True, editable=False, null=True, verbose_name="Estoque baixado em"),
        ),
        migrations.AddField(
            model_name="order",
            name="stock_returned_at",
            field=models.DateTimeField(blank=True, editable=False, null=True, verbose_name="Estoque devolvido em"),
        ),
        migrations.AlterField(
            model_name="order",
            name="delivery_fee",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Calculada pelo backend. Zero enquanto a regra de frete não estiver configurada.",
                max_digits=8,
                verbose_name="Taxa de entrega",
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="delivery_state",
            field=models.CharField(blank=True, max_length=2, verbose_name="Estado (UF)"),
        ),
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Aguardando pagamento"),
                    ("confirmed", "Confirmado"),
                    ("preparing", "Em preparo"),
                    ("ready", "Pronto"),
                    ("delivering", "Em entrega"),
                    ("delivered", "Entregue"),
                    ("cancelled", "Cancelado"),
                ],
                default="pending",
                max_length=20,
                verbose_name="Status",
            ),
        ),
        migrations.AlterField(
            model_name="orderitem",
            name="quantity",
            field=models.PositiveIntegerField(
                default=1,
                validators=[django.core.validators.MinValueValidator(1)],
                verbose_name="Quantidade",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="orderitem",
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name="payment",
            name="amount_paid",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
                verbose_name="Valor pago",
            ),
        ),
        migrations.AlterField(
            model_name="payment",
            name="method",
            field=models.CharField(
                choices=[
                    ("pix", "Pix"),
                    ("credit_card", "Cartão de crédito"),
                    ("debit_card", "Cartão de débito"),
                    ("cash", "Dinheiro"),
                    ("bank_slip", "Boleto"),
                ],
                max_length=20,
                verbose_name="Método",
            ),
        ),
        migrations.AlterField(
            model_name="payment",
            name="transaction_id",
            field=models.CharField(
                blank=True,
                help_text="ID retornado pelo gateway de pagamento.",
                max_length=200,
                verbose_name="ID da transação",
            ),
        ),
        migrations.AddConstraint(
            model_name="order",
            constraint=models.CheckConstraint(
                condition=Q(subtotal__gte=0),
                name="order_subtotal_non_negative",
            ),
        ),
        migrations.AddConstraint(
            model_name="order",
            constraint=models.CheckConstraint(
                condition=Q(discount__gte=0),
                name="order_discount_non_negative",
            ),
        ),
        migrations.AddConstraint(
            model_name="order",
            constraint=models.CheckConstraint(
                condition=Q(delivery_fee__gte=0),
                name="order_delivery_fee_non_negative",
            ),
        ),
        migrations.AddConstraint(
            model_name="order",
            constraint=models.CheckConstraint(
                condition=Q(total__gte=0),
                name="order_total_non_negative",
            ),
        ),
        migrations.AddConstraint(
            model_name="order",
            constraint=models.CheckConstraint(
                condition=Q(discount__lte=F("subtotal")),
                name="order_discount_not_greater_than_subtotal",
            ),
        ),
        migrations.AddConstraint(
            model_name="orderitem",
            constraint=models.UniqueConstraint(
                fields=("order", "product"),
                name="unique_product_per_order",
            ),
        ),
        migrations.AddConstraint(
            model_name="orderitem",
            constraint=models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="order_item_quantity_greater_than_zero",
            ),
        ),
        migrations.AddConstraint(
            model_name="payment",
            constraint=models.CheckConstraint(
                condition=Q(amount_paid__gte=0),
                name="payment_amount_paid_non_negative",
            ),
        ),
    ]

