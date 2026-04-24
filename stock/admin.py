from django.contrib import admin

from .models import StockMovement


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ["product", "movement_type", "quantity", "user", "reason", "created_at"]
    list_filter = ["movement_type", "created_at", "product__category"]
    search_fields = ["product__name", "reason", "user__email"]
    readonly_fields = ["created_at"]
    ordering = ["-created_at"]
    list_per_page = 30
