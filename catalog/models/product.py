"""
catalog/models/product.py

Tabela: produto — corrigida conforme revisão da modelagem:
  - estoque: INT (era VARCHAR → bug em cálculos)
  - preco_custo: adicionado (obrigatório para relatórios de margem)
  - slug: adicionado (obrigatório para URLs e API)
  - destaque / ativo: controle de visibilidade sem deletar
  - created_at / updated_at: rastreabilidade
"""
from decimal import Decimal
from django.db import models
from django.utils.text import slugify
from .category import Category


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,      # PROTECT: impede deletar categoria com produtos
        related_name="products",
        verbose_name="Categoria",
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
    flavor = models.CharField(
        "Sabor / variação",
        max_length=100,
        blank=True,
        help_text="Ex: Chocolate, Red Velvet, Nutella. Opcional.",
    )

    # ── Financeiro ─────────────────────────────────────────────
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
        help_text="Custo de produção por unidade. Visível apenas no admin. "
                  "Usado para calcular margem bruta e lucro.",
    )

    # ── Imagem (Cloudinary em produção) ────────────────────────
    image = models.ImageField(
        "Imagem",
        upload_to="products/",
        null=True,
        blank=True,
    )

    # ── Estoque ────────────────────────────────────────────────
    # CORREÇÃO: era VARCHAR(100) na modelagem original → INT correto
    stock = models.PositiveIntegerField(
        "Estoque",
        default=0,
        help_text="Unidades disponíveis. Decrementado automaticamente a cada pedido.",
    )

    # ── Visibilidade ───────────────────────────────────────────
    is_active = models.BooleanField(
        "Ativo",
        default=True,
        help_text="Desativar oculta o produto da vitrine sem excluí-lo.",
    )
    is_featured = models.BooleanField(
        "Em destaque",
        default=False,
        help_text="Produtos em destaque aparecem primeiro na Home.",
    )

    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ["-is_featured", "name"]

    def __str__(self):
        return f"{self.name} — {self.category.name}"

    # ── Slug único automático ──────────────────────────────────
    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug, n = base, 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    # ── Propriedades calculadas (sem hit extra no banco) ───────
    @property
    def is_in_stock(self) -> bool:
        """True se estoque > 0"""
        return self.stock > 0

    @property
    def gross_margin_pct(self) -> Decimal | None:
        """Margem bruta %: (venda - custo) / venda × 100"""
        if self.cost_price is not None and self.price > 0:
            return ((self.price - self.cost_price) / self.price * 100).quantize(
                Decimal("0.01")
            )
        return None

    @property
    def gross_profit(self) -> Decimal | None:
        """Lucro bruto por unidade: preço_venda - preço_custo"""
        if self.cost_price is not None:
            return self.price - self.cost_price
        return None
