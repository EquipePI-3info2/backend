import logging
from collections import defaultdict
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone

from orders.models import (
    Order,
    OrderItem,
    OrderKitComponent,
    OrderKitItem,
    Payment,
)
from stock.models import StockMovement

logger = logging.getLogger(__name__)


class OrderServiceError(Exception):
    pass


ORDER_TRANSITIONS = {
    Order.Status.PENDING: {Order.Status.CONFIRMED, Order.Status.CANCELLED},
    Order.Status.CONFIRMED: {Order.Status.PREPARING, Order.Status.CANCELLED},
    Order.Status.PREPARING: {Order.Status.READY, Order.Status.CANCELLED},
    Order.Status.READY: {
        Order.Status.DELIVERING,
        Order.Status.DELIVERED,
        Order.Status.CANCELLED,
    },
    Order.Status.DELIVERING: {Order.Status.DELIVERED, Order.Status.CANCELLED},
    Order.Status.DELIVERED: set(),
    Order.Status.CANCELLED: set(),
}

PAYMENT_TRANSITIONS = {
    Payment.Status.PENDING: {
        Payment.Status.APPROVED,
        Payment.Status.REFUSED,
        Payment.Status.CANCELLED,
    },
    Payment.Status.REFUSED: {
        Payment.Status.PENDING,
        Payment.Status.APPROVED,
        Payment.Status.CANCELLED,
    },
    Payment.Status.APPROVED: {Payment.Status.REFUNDED},
    Payment.Status.REFUNDED: set(),
    Payment.Status.CANCELLED: set(),
}


def _raise_stock_error(exc):
    if hasattr(exc, "message_dict"):
        messages = []
        for field_messages in exc.message_dict.values():
            messages.extend(field_messages)
        raise OrderServiceError(" ".join(messages)) from exc
    raise OrderServiceError(str(exc)) from exc


@transaction.atomic
def create_order(
    *,
    user,
    address,
    delivery_method,
    delivery_notes,
    payment_method,
    items,
    kits=None,
):
    kits = kits or []
    payment = Payment.objects.create(
        method=payment_method,
        amount_paid=Decimal("0.00"),
    )

    order_data = {
        "user": user,
        "payment": payment,
        "delivery_method": delivery_method,
        "delivery_notes": delivery_notes,
        "discount": Decimal("0.00"),
        "delivery_fee": Decimal("0.00"),
    }

    if delivery_method == Order.DeliveryMethod.DELIVERY:
        order_data.update(
            {
                "delivery_address": address.full_street,
                "delivery_city": address.city,
                "delivery_state": address.state,
                "delivery_zip": address.zip_code,
            }
        )

    order = Order.objects.create(**order_data)

    OrderItem.objects.bulk_create(
        OrderItem(
            order=order,
            product=item["product"],
            quantity=item["quantity"],
            unit_price=item["product"].price,
        )
        for item in items
    )

    for requested_kit in kits:
        kit = requested_kit["kit"]
        order_kit = OrderKitItem.objects.create(
            order=order,
            kit=kit,
            kit_name=kit.name,
            quantity=requested_kit["quantity"],
            unit_price=kit.promotional_price,
        )
        kit_items = list(
            kit.items.select_related("product").order_by("product_id")
        )
        OrderKitComponent.objects.bulk_create(
            OrderKitComponent(
                order_kit_item=order_kit,
                product=item.product,
                product_name=item.product.name,
                quantity_per_kit=item.quantity,
            )
            for item in kit_items
        )

    order.recalculate_totals()

    logger.info("Pedido %s criado pelo usuário %s.", order.code, user.pk)
    return order


def _stock_requirements(order):
    required = defaultdict(int)
    products = {}

    for item in order.items.select_related("product").order_by("product_id"):
        required[item.product_id] += item.quantity
        products[item.product_id] = item.product

    kit_items = order.kit_items.prefetch_related(
        "components__product"
    ).order_by("id")

    for kit_item in kit_items:
        for component in kit_item.components.all():
            required[component.product_id] += (
                component.quantity_per_kit * kit_item.quantity
            )
            products[component.product_id] = component.product

    return [
        (products[product_id], required[product_id])
        for product_id in sorted(required)
    ]


def _deduct_order_stock(order, actor):
    if order.stock_deducted_at is not None:
        return

    for product, quantity in _stock_requirements(order):
        try:
            StockMovement.objects.create(
                product=product,
                order=order,
                user=actor,
                movement_type=StockMovement.MovementType.OUT,
                quantity=quantity,
                reason=f"Venda confirmada do pedido {order.code}",
            )
        except DjangoValidationError as exc:
            _raise_stock_error(exc)

    order.stock_deducted_at = timezone.now()


def _return_order_stock(order, actor):
    if order.stock_deducted_at is None or order.stock_returned_at is not None:
        return

    for product, quantity in _stock_requirements(order):
        StockMovement.objects.create(
            product=product,
            order=order,
            user=actor,
            movement_type=StockMovement.MovementType.RETURN,
            quantity=quantity,
            reason=f"Cancelamento do pedido {order.code}",
        )

    order.stock_returned_at = timezone.now()


@transaction.atomic
def transition_order_status(*, order, new_status, actor):
    order = (
        Order.objects.select_for_update(of=("self",))
        .select_related("payment", "user")
        .get(pk=order.pk)
    )

    if new_status == order.status:
        return order

    allowed = ORDER_TRANSITIONS.get(order.status, set())
    if new_status not in allowed:
        raise OrderServiceError(
            f"Não é permitido alterar o pedido de "
            f"'{order.get_status_display()}' para "
            f"'{Order.Status(new_status).label}'."
        )

    if new_status == Order.Status.CONFIRMED:
        if (
            order.payment is None
            or order.payment.status != Payment.Status.APPROVED
        ):
            raise OrderServiceError(
                "O pedido somente pode ser confirmado "
                "após a aprovação do pagamento."
            )

        _deduct_order_stock(order, actor)
        order.mark_confirmed()

    if new_status == Order.Status.DELIVERING:
        if order.delivery_method != Order.DeliveryMethod.DELIVERY:
            raise OrderServiceError(
                "Pedidos para retirada não podem ser "
                "marcados como 'Em entrega'."
            )

    if new_status == Order.Status.DELIVERED:
        if (
            order.delivery_method == Order.DeliveryMethod.DELIVERY
            and order.status != Order.Status.DELIVERING
        ):
            raise OrderServiceError(
                "Pedidos com entrega devem passar "
                "pelo status 'Em entrega'."
            )

        order.mark_delivered()

    if new_status == Order.Status.CANCELLED:
        if (
            order.payment
            and order.payment.status == Payment.Status.APPROVED
        ):
            raise OrderServiceError(
                "Estorne o pagamento aprovado antes de cancelar o pedido."
            )

        _return_order_stock(order, actor)
        order.mark_cancelled()

        if (
            order.payment
            and order.payment.status == Payment.Status.PENDING
        ):
            order.payment.status = Payment.Status.CANCELLED
            order.payment.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

    previous_status = order.status
    order.status = new_status

    order.save(
        update_fields=[
            "status",
            "confirmed_at",
            "delivered_at",
            "cancelled_at",
            "stock_deducted_at",
            "stock_returned_at",
            "updated_at",
        ]
    )

    logger.info(
        "Status do pedido %s alterado de %s para %s pelo usuário %s.",
        order.code,
        previous_status,
        new_status,
        actor.pk,
    )

    return order


@transaction.atomic
def cancel_order(*, order, actor):
    if (
        not actor.is_staff
        and order.status != Order.Status.PENDING
    ):
        raise OrderServiceError(
            "O cliente somente pode cancelar um pedido "
            "que ainda aguarda pagamento."
        )

    return transition_order_status(
        order=order,
        new_status=Order.Status.CANCELLED,
        actor=actor,
    )


@transaction.atomic
def update_payment_status(
    *,
    payment,
    new_status,
    actor,
    transaction_id="",
    amount_paid=None,
):
    payment = (
        Payment.objects.select_for_update(of=("self",))
        .select_related("order")
        .get(pk=payment.pk)
    )

    try:
        order = payment.order
    except Order.DoesNotExist as exc:
        raise OrderServiceError(
            "O pagamento não está associado a um pedido."
        ) from exc

    if new_status == payment.status:
        return payment

    allowed = PAYMENT_TRANSITIONS.get(payment.status, set())

    if new_status not in allowed:
        raise OrderServiceError(
            f"Não é permitido alterar o pagamento de "
            f"'{payment.get_status_display()}' para "
            f"'{Payment.Status(new_status).label}'."
        )

    if (
        order.status == Order.Status.CANCELLED
        and new_status == Payment.Status.APPROVED
    ):
        raise OrderServiceError(
            "Não é possível aprovar o pagamento de um pedido cancelado."
        )

    previous_status = payment.status
    payment.status = new_status

    if transaction_id:
        payment.transaction_id = transaction_id

    if new_status == Payment.Status.APPROVED:
        expected_amount = order.total

        paid_value = (
            expected_amount
            if amount_paid is None
            else amount_paid
        )

        if paid_value != expected_amount:
            raise OrderServiceError(
                f"O valor aprovado deve ser exatamente "
                f"R$ {expected_amount}."
            )

        payment.amount_paid = paid_value
        payment.paid_at = timezone.now()

    elif new_status in {
        Payment.Status.PENDING,
        Payment.Status.REFUSED,
        Payment.Status.CANCELLED,
    }:
        payment.amount_paid = Decimal("0.00")
        payment.paid_at = None

    payment.save(
        update_fields=[
            "status",
            "amount_paid",
            "transaction_id",
            "paid_at",
            "updated_at",
        ]
    )

    if new_status == Payment.Status.APPROVED:
        transition_order_status(
            order=order,
            new_status=Order.Status.CONFIRMED,
            actor=actor,
        )

    elif new_status in {
        Payment.Status.CANCELLED,
        Payment.Status.REFUNDED,
    }:
        if order.status != Order.Status.CANCELLED:
            transition_order_status(
                order=order,
                new_status=Order.Status.CANCELLED,
                actor=actor,
            )

    logger.info(
        "Status do pagamento %s alterado de %s para %s pelo usuário %s.",
        payment.pk,
        previous_status,
        new_status,
        actor.pk,
    )

    return payment
