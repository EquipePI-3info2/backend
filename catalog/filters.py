import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):
    """
    Filtros disponíveis em GET /api/products/
      ?category=cookies          → por slug de categoria
      ?price_min=5&price_max=15  → faixa de preço
      ?is_featured=true          → somente destaques
      ?in_stock=true             → somente com estoque > 0
    """
    category    = django_filters.CharFilter(field_name="category__slug", lookup_expr="iexact")
    price_min   = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max   = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    is_featured = django_filters.BooleanFilter(field_name="is_featured")
    in_stock    = django_filters.BooleanFilter(method="filter_in_stock")

    def filter_in_stock(self, queryset, name, value):
        return queryset.filter(stock__gt=0) if value else queryset

    class Meta:
        model  = Product
        fields = ["category", "price_min", "price_max", "is_featured", "in_stock"]
