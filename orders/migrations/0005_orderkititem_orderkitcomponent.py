import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0005_kit_kititem"),
        ("orders", "0004_complete_order_workflow"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrderKitItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kit_name", models.CharField(max_length=150, verbose_name="Nome do kit")),
                ("quantity", models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)], verbose_name="Quantidade")),
                ("unit_price", models.DecimalField(decimal_places=2, help_text="Preço promocional salvo no momento da compra.", max_digits=8, verbose_name="Preço unitário")),
                ("kit", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="order_items", to="catalog.kit", verbose_name="Kit")),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="kit_items", to="orders.order", verbose_name="Pedido")),
            ],
            options={
                "verbose_name": "Kit do pedido",
                "verbose_name_plural": "Kits do pedido",
            },
        ),
        migrations.CreateModel(
            name="OrderKitComponent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("product_name", models.CharField(max_length=150, verbose_name="Nome do produto")),
                ("quantity_per_kit", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name="Quantidade por kit")),
                ("order_kit_item", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="components", to="orders.orderkititem", verbose_name="Kit do pedido")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="order_kit_components", to="catalog.product", verbose_name="Produto")),
            ],
            options={
                "verbose_name": "Componente do kit no pedido",
                "verbose_name_plural": "Componentes dos kits nos pedidos",
            },
        ),
        migrations.AddConstraint(
            model_name="orderkititem",
            constraint=models.UniqueConstraint(fields=("order", "kit"), name="unique_kit_per_order"),
        ),
        migrations.AddConstraint(
            model_name="orderkititem",
            constraint=models.CheckConstraint(condition=models.Q(("quantity__gt", 0)), name="order_kit_item_quantity_greater_than_zero"),
        ),
        migrations.AddConstraint(
            model_name="orderkitcomponent",
            constraint=models.UniqueConstraint(fields=("order_kit_item", "product"), name="unique_product_per_order_kit"),
        ),
        migrations.AddConstraint(
            model_name="orderkitcomponent",
            constraint=models.CheckConstraint(condition=models.Q(("quantity_per_kit__gt", 0)), name="order_kit_component_quantity_greater_than_zero"),
        ),
    ]
