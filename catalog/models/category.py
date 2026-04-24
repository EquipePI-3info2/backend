"""
catalog/models/category.py

Tabela: categoria
  - PK int (BigAutoField) — consistente com DEFAULT_AUTO_FIELD do projeto
  - Imagem via ImageField: usa Cloudinary em produção automaticamente
    (django-cloudinary-storage já configurado no settings.py)
  - slug gerado automaticamente a partir do nome
  - ativo / ordem para controle de exibição na vitrine
"""
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField("Nome", max_length=150)
    slug = models.SlugField(
        "Slug",
        max_length=160,
        unique=True,
        blank=True,
        help_text="Gerado automaticamente. Usado em URLs e no filtro ?category=slug da API.",
    )
    description = models.TextField("Descrição", blank=True)
    image = models.ImageField(
        "Imagem",
        upload_to="categories/",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(
        "Ativo",
        default=True,
        help_text="Categorias inativas ficam ocultas na vitrine sem serem excluídas.",
    )
    order = models.PositiveSmallIntegerField(
        "Ordem de exibição",
        default=0,
        help_text="Menor número = aparece primeiro. Controla a sequência das pills na Home.",
    )
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
