"""
catalog/migrations/0002_flavor_alter_product_cost_price_and_more.py

MIGRAÇÃO CORRIGIDA — 3 passos em uma só migration:

  Passo 1 (SchemaEditor): Cria a tabela catalog_flavor e adiciona
           catalog_product.flavor_id como coluna NULLABLE.

  Passo 2 (RunPython): Lê o texto do antigo campo flavor em cada produto,
           cria o Flavor correspondente se não existir, e preenche flavor_id.

  Passo 3 (SchemaEditor): Remove a coluna antiga flavor (VARCHAR) e,
           opcionalmente, torna flavor_id NOT NULL se quiser.
           Por ora mantemos NULL para produtos sem sabor definido.

Demais alterações de campos (cost_price, is_active, etc.) seguem normais.
"""

from django.db import migrations, models
import django.db.models.deletion


def create_flavors_from_text(apps, schema_editor):
    """
    Percorre todos os produtos com flavor_text preenchido,
    cria o Flavor correspondente e atribui flavor_id.
    """
    Product = apps.get_model("catalog", "Product")
    Flavor  = apps.get_model("catalog", "Flavor")

    from django.utils.text import slugify

    for product in Product.objects.exclude(flavor_text__isnull=True).exclude(flavor_text=""):
        name = product.flavor_text.strip()
        if not name:
            continue

        flavor, _ = Flavor.objects.get_or_create(
            slug=slugify(name),
            defaults={"name": name, "description": "", "is_active": True},
        )
        product.flavor = flavor
        product.save(update_fields=["flavor"])


def reverse_flavors(apps, schema_editor):
    """
    Reverte: copia o nome do Flavor de volta para flavor_text.
    """
    Product = apps.get_model("catalog", "Product")

    for product in Product.objects.filter(flavor__isnull=False):
        product.flavor_text = product.flavor.name
        product.save(update_fields=["flavor_text"])


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        # ── 1. Cria a tabela Flavor ──────────────────────────────────────────
        migrations.CreateModel(
            name="Flavor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name",        models.CharField(max_length=100, unique=True, verbose_name="Nome")),
                ("slug",        models.SlugField(blank=True, help_text="Gerado automaticamente.", max_length=120, unique=True, verbose_name="Slug")),
                ("description", models.TextField(blank=True, verbose_name="Descrição")),
                ("is_active",   models.BooleanField(default=True, verbose_name="Ativo")),
                ("created_at",  models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at",  models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
            ],
            options={
                "verbose_name": "Sabor",
                "verbose_name_plural": "Sabores",
                "ordering": ["name"],
            },
        ),

        # ── 2. Renomeia o campo texto antigo para flavor_text (backup) ───────
        migrations.RenameField(
            model_name="product",
            old_name="flavor",
            new_name="flavor_text",
        ),

        # ── 3. Adiciona flavor_id (FK, NULL por ora) ─────────────────────────
        migrations.AddField(
            model_name="product",
            name="flavor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="products",
                to="catalog.flavor",
                verbose_name="Sabor",
            ),
        ),

        # ── 4. Migração de dados: cria Flavors e preenche flavor_id ──────────
        migrations.RunPython(create_flavors_from_text, reverse_code=reverse_flavors),

        # ── 5. Remove a coluna texto antiga ──────────────────────────────────
        migrations.RemoveField(
            model_name="product",
            name="flavor_text",
        ),

        # ── 6. Demais alterações de campos do produto ─────────────────────────
        migrations.AlterField(
            model_name="product",
            name="cost_price",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Custo de produção por unidade. Visível apenas no admin.",
                max_digits=8,
                null=True,
                verbose_name="Preço de custo",
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="Ativo"),
        ),
        migrations.AlterField(
            model_name="product",
            name="is_featured",
            field=models.BooleanField(default=False, verbose_name="Em destaque"),
        ),
        migrations.AlterField(
            model_name="product",
            name="stock",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Unidades disponíveis. Decrementado automaticamente via signal.",
                verbose_name="Estoque",
            ),
        ),
    ]
