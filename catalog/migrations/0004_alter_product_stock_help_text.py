from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0003_alter_flavor_slug_alter_product_flavor"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="stock",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Unidades disponíveis. Atualizado pelas movimentações de estoque.",
                verbose_name="Estoque",
            ),
        ),
    ]