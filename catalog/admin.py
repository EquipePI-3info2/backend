from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display        = ["name", "slug", "is_active", "order", "product_count", "updated_at"]
    list_editable       = ["is_active", "order"]
    list_filter         = ["is_active"]
    search_fields       = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields     = ["created_at", "updated_at"]
    ordering            = ["order", "name"]

    @admin.display(description="Produtos")
    def product_count(self, obj):
        return obj.products.count()


class StockStatusFilter(admin.SimpleListFilter):
    title            = "Estoque"
    parameter_name   = "stock_status"

    def lookups(self, request, model_admin):
        return [("in", "Em estoque"), ("out", "Sem estoque")]

    def queryset(self, request, queryset):
        if self.value() == "in":
            return queryset.filter(stock__gt=0)
        if self.value() == "out":
            return queryset.filter(stock=0)
        return queryset


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display        = [
        "thumbnail", "name", "category", "price", "cost_price",
        "margin_display", "stock", "is_active", "is_featured", "updated_at",
    ]
    list_editable       = ["price", "stock", "is_active", "is_featured"]
    list_filter         = ["is_active", "is_featured", "category", StockStatusFilter]
    search_fields       = ["name", "description", "slug", "flavor"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields     = ["margin_display", "created_at", "updated_at"]
    autocomplete_fields = ["category"]
    ordering            = ["-is_featured", "name"]
    list_per_page       = 25

    fieldsets = [
        ("Identificação", {
            "fields": ("name", "slug", "category", "flavor", "description"),
        }),
        ("Financeiro", {
            "fields": ("price", "cost_price", "margin_display"),
            "description": "cost_price é visível apenas no painel admin.",
        }),
        ("Estoque e visibilidade", {
            "fields": ("stock", "is_active", "is_featured", "image"),
        }),
        ("Metadados", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    ]

    @admin.display(description="")
    def thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="40" height="40" '
                'style="object-fit:cover;border-radius:6px">',
                obj.image.url,
            )
        return "—"

    @admin.display(description="Margem %", ordering="price")
    def margin_display(self, obj):
        m = obj.gross_margin_pct
        if m is None:
            return "—"
        cor = "#2e7d32" if m >= 30 else "#e65100"
        return format_html('<b style="color:{}">{} %</b>', cor, m)
