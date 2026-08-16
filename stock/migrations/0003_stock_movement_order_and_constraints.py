import django.core.validators
import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0004_complete_order_workflow"),
        ("stock", "0002_alter_stockmovement_movement_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="stockmovement",
            name="order",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="stock_movements",
                to="orders.order",
                verbose_name="Pedido",
            ),
        ),
        migrations.AlterField(
            model_name="stockmovement",
            name="quantity",
            field=models.PositiveIntegerField(
                help_text="Sempre positivo. O tipo determina se entra ou sai do estoque.",
                validators=[django.core.validators.MinValueValidator(1)],
                verbose_name="Quantidade",
            ),
        ),
        migrations.AddConstraint(
            model_name="stockmovement",
            constraint=models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="stock_movement_quantity_greater_than_zero",
            ),
        ),
    ]