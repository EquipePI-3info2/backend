# Generated for the Brookiê address module.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0019_remove_produto_categoria_remove_pedido_pagamento_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Address",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "label",
                    models.CharField(
                        blank=True,
                        help_text="Ex.: Casa, Trabalho.",
                        max_length=50,
                        verbose_name="Identificação",
                    ),
                ),
                ("street", models.CharField(max_length=200, verbose_name="Logradouro")),
                ("number", models.CharField(max_length=20, verbose_name="Número")),
                (
                    "complement",
                    models.CharField(
                        blank=True,
                        max_length=100,
                        verbose_name="Complemento",
                    ),
                ),
                (
                    "neighborhood",
                    models.CharField(max_length=100, verbose_name="Bairro"),
                ),
                ("city", models.CharField(max_length=100, verbose_name="Cidade")),
                ("state", models.CharField(max_length=2, verbose_name="Estado (UF)")),
                ("zip_code", models.CharField(max_length=9, verbose_name="CEP")),
                (
                    "is_default",
                    models.BooleanField(default=False, verbose_name="Endereço padrão"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criado em"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Atualizado em"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="addresses",
                        to="core.user",
                        verbose_name="Usuário",
                    ),
                ),
            ],
            options={
                "verbose_name": "Endereço",
                "verbose_name_plural": "Endereços",
                "ordering": ["-is_default", "-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="address",
            constraint=models.UniqueConstraint(
                condition=models.Q(is_default=True),
                fields=("user",),
                name="unique_default_address_per_user",
            ),
        ),
    ]