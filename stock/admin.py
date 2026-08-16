from django.contrib import admin

from .models import StockMovement


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = [
        "product",
        "movement_type",
        "quantity",
        "order",
        "user",
        "reason",
        "created_at",
    ]
    list_filter = ["movement_type", "created_at", "product__category"]
    search_fields = ["product__name", "order__code", "reason", "user__email"]
    readonly_fields = ["created_at"]
    ordering = ["-created_at"]
    list_per_page = 30

    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return [
                "product",
                "movement_type",
                "quantity",
                "order",
                "user",
                "reason",
                "created_at",
            ]
        return self.readonly_fields

    def has_delete_permission(self, request, obj=None):
        return False
