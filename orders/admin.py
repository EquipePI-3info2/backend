from django.contrib import admin
from django.utils.html import format_html

from .models import Order, OrderItem, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["subtotal_display"]
    fields = ["product", "quantity", "unit_price", "subtotal_display"]

    @admin.display(description="Subtotal")
    def subtotal_display(self, obj):
        return f"R$ {obj.subtotal:.2f}"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["code", "user", "status_badge", "total", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["code", "user__email", "user__name"]
    readonly_fields = ["code", "created_at", "updated_at"]
    inlines = [OrderItemInline]
    ordering = ["-created_at"]

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            "pending":    "#f59e0b",
            "confirmed":  "#3b82f6",
            "preparing":  "#8b5cf6",
            "ready":      "#06b6d4",
            "delivering": "#f97316",
            "delivered":  "#22c55e",
            "cancelled":  "#ef4444",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:9999px;font-size:12px">{}</span>',
            color, obj.get_status_display()
        )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "method", "status", "amount_paid", "paid_at", "created_at"]
    list_filter = ["status", "method"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]
