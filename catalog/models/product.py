"""
catalog/models/product.py
"""
from decimal import Decimal

from django.db import models
from django.utils.text import slugify

from .category import Category
from .flavor import Flavor


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="Categoria",
    )
    flavor = models.ForeignKey(
        Flavor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="Sabor",
        help_text="Sabor principal do produto. Deixe em branco se não se aplica.",
    )
    name = models.CharField("Nome", max_length=150)
    slug = models.SlugField(
        "Slug",
        max_length=170,
        unique=True,
        blank=True,
        help_text="Gerado automaticamente. Usado em URLs como /produto/cookie-classico/",
    )
    description = models.TextField("Descrição", blank=True)

    # ── Financeiro ────────────────────────────────────────────
    price = models.DecimalField(
        "Preço de venda",
        max_digits=8,
        decimal_places=2,
        help_text="Valor exibido ao cliente (R$).",
    )
    cost_price = models.DecimalField(
        "Preço de custo",
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Custo de produção por unidade. Visível apenas no admin.",
    )

    # ── Imagem ────────────────────────────────────────────────
    # Decisão: 1 imagem por produto no MVP.
    # Para múltiplas imagens: criar ProductImage(FK→Product, image, order).
    image = models.ImageField(
        "Imagem",
        upload_to="products/",
        null=True,
        blank=True,
    )

    # ── Estoque ───────────────────────────────────────────────
    stock = models.PositiveIntegerField(
        "Estoque",
        default=0,
        help_text="Unidades disponíveis. Decrementado automaticamente via signal.",
    )

    # ── Visibilidade ──────────────────────────────────────────
    is_active = models.BooleanField("Ativo", default=True)
    is_featured = models.BooleanField("Em destaque", default=False)

    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ["-is_featured", "name"]

    def __str__(self):
        return f"{self.name} — {self.category.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug, n = base, 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    # ── Propriedades calculadas ───────────────────────────────
    @property
    def is_in_stock(self) -> bool:
        return self.stock > 0

    @property
    def gross_margin_pct(self) -> Decimal | None:
        if self.cost_price is not None and self.price > 0:
            return ((self.price - self.cost_price) / self.price * 100).quantize(
                Decimal("0.01")
            )
        return None

    @property
    def gross_profit(self) -> Decimal | None:
        if self.cost_price is not None:
            return self.price - self.cost_price
        return None
