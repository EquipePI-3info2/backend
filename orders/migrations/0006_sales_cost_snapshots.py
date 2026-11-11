from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("orders", "0005_orderkititem_orderkitcomponent")]

    operations = [
        migrations.AddField(
            model_name=model_name,
            name="unit_cost",
            field=models.DecimalField(
                "Custo unitário na venda",
                max_digits=8,
                decimal_places=2,
                null=True,
                blank=True,
            ),
        )
        for model_name in ("orderitem", "orderkitcomponent")
    ]
