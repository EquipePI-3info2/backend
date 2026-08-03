from django.contrib import admin, messages
from django.utils.html import format_html

from orders.models import Order, OrderItem, Payment
from orders.services import (
    OrderServiceError,
    transition_order_status,
    update_payment_status,
)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    fields = ["product", "quantity", "unit_price", "subtotal_display"]
    readonly_fields = fields

    @admin.display(description="Subtotal")
    def subtotal_display(self, obj):
        return f"R$ {obj.subtotal:.2f}" if obj.pk else "-"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["code", "user", "status_badge", "total", "created_at"]
    list_filter = ["status", "delivery_method", "created_at"]
    search_fields = ["code", "user__email", "user__name"]
    ordering = ["-created_at"]
    inlines = [OrderItemInline]
    actions = [
        "confirm_orders",
        "mark_preparing",
        "mark_ready",
        "mark_delivering",
        "mark_delivered",
        "cancel_orders",
    ]
    readonly_fields = [
        "code",
        "user",
        "payment",
        "status",
        "subtotal",
        "discount",
        "delivery_fee",
        "total",
        "delivery_method",
        "delivery_address",
        "delivery_city",
        "delivery_state",
        "delivery_zip",
        "delivery_notes",
        "created_at",
        "updated_at",
        "confirmed_at",
        "delivered_at",
        "cancelled_at",
        "stock_deducted_at",
        "stock_returned_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            Order.Status.PENDING: "#f59e0b",
            Order.Status.CONFIRMED: "#3b82f6",
            Order.Status.PREPARING: "#8b5cf6",
            Order.Status.READY: "#06b6d4",
            Order.Status.DELIVERING: "#f97316",
            Order.Status.DELIVERED: "#22c55e",
            Order.Status.CANCELLED: "#ef4444",
        }
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:9999px;font-size:12px">{}</span>',
            colors.get(obj.status, "#6b7280"),
            obj.get_status_display(),
        )

    def _transition(self, request, queryset, new_status):
        success = 0
        errors = []
        for order in queryset:
            try:
                transition_order_status(
                    order=order,
                    new_status=new_status,
                    actor=request.user,
                )
                success += 1
            except OrderServiceError as exc:
                errors.append(f"{order.code}: {exc}")

        if success:
            self.message_user(
                request,
                f"{success} pedido(s) atualizado(s).",
                level=messages.SUCCESS,
            )
        for error in errors:
            self.message_user(request, error, level=messages.ERROR)

    @admin.action(description="Confirmar pedidos selecionados")
    def confirm_orders(self, request, queryset):
        self._transition(request, queryset, Order.Status.CONFIRMED)

    @admin.action(description="Marcar como em preparo")
    def mark_preparing(self, request, queryset):
        self._transition(request, queryset, Order.Status.PREPARING)

    @admin.action(description="Marcar como pronto")
    def mark_ready(self, request, queryset):
        self._transition(request, queryset, Order.Status.READY)

    @admin.action(description="Marcar como em entrega")
    def mark_delivering(self, request, queryset):
        self._transition(request, queryset, Order.Status.DELIVERING)

    @admin.action(description="Marcar como entregue")
    def mark_delivered(self, request, queryset):
        self._transition(request, queryset, Order.Status.DELIVERED)

    @admin.action(description="Cancelar pedidos selecionados")
    def cancel_orders(self, request, queryset):
        self._transition(request, queryset, Order.Status.CANCELLED)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "order_code",
        "method",
        "status",
        "amount_paid",
        "paid_at",
        "created_at",
    ]
    list_filter = ["status", "method"]
    search_fields = ["transaction_id", "order__code", "order__user__email"]
    ordering = ["-created_at"]
    readonly_fields = [
        "method",
        "status",
        "amount_paid",
        "paid_at",
        "created_at",
        "updated_at",
    ]
    actions = ["approve_payments", "refuse_payments", "refund_payments"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Pedido")
    def order_code(self, obj):
        try:
            return obj.order.code
        except Order.DoesNotExist:
            return "-"

    def _change_status(self, request, queryset, new_status):
        success = 0
        errors = []
        for payment in queryset:
            try:
                update_payment_status(
                    payment=payment,
                    new_status=new_status,
                    actor=request.user,
                )
                success += 1
            except OrderServiceError as exc:
                errors.append(f"Pagamento {payment.pk}: {exc}")

        if success:
            self.message_user(
                request,
                f"{success} pagamento(s) atualizado(s).",
                level=messages.SUCCESS,
            )
        for error in errors:
            self.message_user(request, error, level=messages.ERROR)

    @admin.action(description="Aprovar pagamentos selecionados")
    def approve_payments(self, request, queryset):
        self._change_status(request, queryset, Payment.Status.APPROVED)

    @admin.action(description="Recusar pagamentos selecionados")
    def refuse_payments(self, request, queryset):
        self._change_status(request, queryset, Payment.Status.REFUSED)

    @admin.action(description="Estornar pagamentos selecionados")
    def refund_payments(self, request, queryset):
        self._change_status(request, queryset, Payment.Status.REFUNDED)