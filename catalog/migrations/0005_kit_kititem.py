from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0004_alter_product_stock_help_text"),
    ]

    operations = [
        migrations.CreateModel(
            name="Kit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150, verbose_name="Nome")),
                ("slug", models.SlugField(blank=True, help_text="Gerado automaticamente e usado nas URLs do kit.", max_length=170, unique=True, verbose_name="Slug")),
                ("description", models.TextField(blank=True, verbose_name="Descrição")),
                ("promotional_price", models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(Decimal("0.01"))], verbose_name="Preço promocional")),
                ("image", models.ImageField(blank=True, null=True, upload_to="kits/", verbose_name="Imagem")),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("is_featured", models.BooleanField(default=False, verbose_name="Em destaque")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
            ],
            options={
                "verbose_name": "Kit",
                "verbose_name_plural": "Kits",
                "ordering": ["-is_featured", "name"],
            },
        ),
        migrations.CreateModel(
            name="KitItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)], verbose_name="Quantidade")),
                ("kit", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="catalog.kit", verbose_name="Kit")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="kit_items", to="catalog.product", verbose_name="Produto")),
            ],
            options={
                "verbose_name": "Item do kit",
                "verbose_name_plural": "Itens do kit",
                "ordering": ["id"],
            },
        ),
        migrations.AddConstraint(
            model_name="kititem",
            constraint=models.UniqueConstraint(fields=("kit", "product"), name="unique_product_per_kit"),
        ),
        migrations.AddConstraint(
            model_name="kititem",
            constraint=models.CheckConstraint(condition=models.Q(("quantity__gt", 0)), name="kit_item_quantity_greater_than_zero"),
        ),
    ]
