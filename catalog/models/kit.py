from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify

from .product import Product


class Kit(models.Model):
    name = models.CharField("Nome", max_length=150)
    slug = models.SlugField(
        "Slug",
        max_length=170,
        unique=True,
        blank=True,
        help_text="Gerado automaticamente e usado nas URLs do kit.",
    )
    description = models.TextField("Descrição", blank=True)
    promotional_price = models.DecimalField(
        "Preço promocional",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    image = models.ImageField(
        "Imagem",
        upload_to="kits/",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField("Ativo", default=True)
    is_featured = models.BooleanField("Em destaque", default=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Kit"
        verbose_name_plural = "Kits"
        ordering = ["-is_featured", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug, n = base, 1
            while Kit.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def _component_items(self):
        prefetched = getattr(self, "_prefetched_objects_cache", {}).get("items")
        if prefetched is not None:
            return list(prefetched)
        return list(self.items.select_related("product", "product__category").all())

    @property
    def regular_price(self) -> Decimal:
        total = Decimal("0.00")
        for item in self._component_items():
            total += item.product.price * item.quantity
        return total

    @property
    def savings(self) -> Decimal:
        return max(self.regular_price - self.promotional_price, Decimal("0.00"))

    @property
    def available_stock(self) -> int:
        items = self._component_items()
        if not items:
            return 0

        available = []
        for item in items:
            product = item.product
            if not product.is_active or not product.category.is_active:
                return 0
            available.append(product.stock // item.quantity)
        return min(available) if available else 0

    @property
    def is_in_stock(self) -> bool:
        return self.available_stock > 0


class KitItem(models.Model):
    kit = models.ForeignKey(
        Kit,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Kit",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="kit_items",
        verbose_name="Produto",
    )
    quantity = models.PositiveIntegerField(
        "Quantidade",
        default=1,
        validators=[MinValueValidator(1)],
    )

    class Meta:
        verbose_name = "Item do kit"
        verbose_name_plural = "Itens do kit"
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["kit", "product"],
                name="unique_product_per_kit",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="kit_item_quantity_greater_than_zero",
            ),
        ]

    def __str__(self):
        return f"{self.quantity}x {self.product.name} — {self.kit.name}"
