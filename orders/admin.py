from django.contrib import admin

from .models import Order, OrderItem, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "user",
        "status",
        "total",
        "created_at",
    )

    search_fields = (
        "code",
        "user__name",
        "user__email",
    )

    list_filter = (
        "status",
        "created_at",
    )

    inlines = [
        OrderItemInline,
    ]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "method",
        "status",
        "amount_paid",
        "paid_at",
    )
