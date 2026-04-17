"""
catalog/models/flavor.py

Entidade separada para Sabor — sugestão do professor.

Por que entidade própria e não CharField no Produto?
  - Sabores se repetem entre produtos: Chocolate, Nutella, Red Velvet aparecem
    em cookies E brownies. Uma entidade evita inconsistência de digitação.
  - Permite filtros de catálogo por sabor (?flavor=chocolate).
  - Permite relatórios de sabores mais vendidos.
  - Permite associar imagem ou cor ao sabor no futuro.

Relação com Produto: ForeignKey (um produto tem um sabor principal).
Evolução futura: ManyToMany se um produto puder ter vários sabores.
"""
from django.db import models
from django.utils.text import slugify


class Flavor(models.Model):
    name = models.CharField("Nome", max_length=100, unique=True)
    slug = models.SlugField(
        "Slug",
        max_length=120,
        unique=True,
        blank=True,
        help_text="Gerado automaticamente. Usado em filtros de API.",
    )
    description = models.TextField("Descrição", blank=True)
    is_active   = models.BooleanField("Ativo", default=True)
    created_at  = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at  = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name        = "Sabor"
        verbose_name_plural = "Sabores"
        ordering            = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
