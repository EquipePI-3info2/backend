from collections import defaultdict
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Prefetch
from django.utils import timezone

from orders.models import OrderItem, OrderKitItem, Payment

ZERO = Decimal("0.00")
PERIODS = ("day", "week", "month", "year")


def _period_bounds(reference, period):
    if period == "day":
        return reference, reference + timedelta(days=1)
    if period == "week":
        start = reference - timedelta(days=reference.weekday())
        return start, start + timedelta(days=7)
    if period == "month":
        start = reference.replace(day=1)
        return start, (start + timedelta(days=32)).replace(day=1)
    start = reference.replace(month=1, day=1)
    return start, start.replace(year=start.year + 1)


def _start_of_day(value):
    return timezone.make_aware(datetime.combine(value, time.min))


def _percentage(amount, base):
    if base:
        return (amount * 100 / base).quantize(Decimal("0.01"))
    return None if amount else ZERO


def _bucket(date, period):
    if period == "year":
        return date.replace(day=1)
    return date


def _next_bucket(date, period):
    if period == "year":
        return (date + timedelta(days=32)).replace(day=1)
    return date + timedelta(days=1)


def _record(rows, key, name, quantity, revenue=None):
    row = rows.setdefault(key, {"id": key, "name": name, "quantity": 0, "revenue": ZERO})
    row["quantity"] += quantity
    if revenue is not None:
        row["revenue"] += revenue
        row["sold_separately"] = True


def get_dashboard(period="week", reference_date=None):
    reference_date = reference_date or timezone.localdate()
    start, end = _period_bounds(reference_date, period)
    previous_start, _ = _period_bounds(start - timedelta(days=1), period)

    payments = (
        Payment.objects.filter(
            status=Payment.Status.APPROVED,
            paid_at__gte=_start_of_day(previous_start),
            paid_at__lt=_start_of_day(min(end, reference_date + timedelta(days=1))),
        )
        .select_related("order")
        .prefetch_related(
            Prefetch("order__items", queryset=OrderItem.objects.select_related("product")),
            Prefetch("order__kit_items", queryset=OrderKitItem.objects.prefetch_related("components")),
        )
        .order_by("paid_at", "pk")
    )

    gross = discounts = delivery = received = previous_received = cost = ZERO
    missing_cost_orders = unmatched_payments = 0
    products, kits, methods = {}, {}, {}
    series = defaultdict(lambda: ZERO)

    for payment in payments:
        date = timezone.localdate(payment.paid_at)
        if date < start:
            previous_received += payment.amount_paid
            continue

        received += payment.amount_paid
        series[_bucket(date, period)] += payment.amount_paid
        method = methods.setdefault(
            payment.method,
            {"method": payment.method, "name": payment.get_method_display(), "revenue": ZERO},
        )
        method["revenue"] += payment.amount_paid

        order = getattr(payment, "order", None)
        if order is None:
            unmatched_payments += 1
            continue

        gross += order.subtotal
        discounts += order.discount
        delivery += order.delivery_fee
        cost_complete = True
        items = list(order.items.all())
        kit_items = list(order.kit_items.all())
        if not items and not kit_items and order.subtotal:
            cost_complete = False

        for item in items:
            _record(products, item.product_id, item.product.name, item.quantity, item.subtotal)
            if item.unit_cost is None:
                cost_complete = False
            else:
                cost += item.quantity * item.unit_cost

        for kit in kit_items:
            _record(kits, kit.kit_id, kit.kit_name, kit.quantity, kit.subtotal)
            components = list(kit.components.all())
            if not components:
                cost_complete = False
            for component in components:
                quantity = kit.quantity * component.quantity_per_kit
                _record(products, component.product_id, component.product_name, quantity)
                if component.unit_cost is None:
                    cost_complete = False
                else:
                    cost += quantity * component.unit_cost

        missing_cost_orders += int(not cost_complete)

    net = gross - discounts
    profit = None if missing_cost_orders or unmatched_payments else net - cost
    points = []
    bucket = start
    while bucket < end and bucket <= reference_date:
        points.append({"date": bucket, "revenue": series[bucket]})
        bucket = _next_bucket(bucket, period)

    return {
        "period": period,
        "current_period": {"start": start, "end": end - timedelta(days=1), "revenue": received},
        "previous_period": {
            "start": previous_start, "end": start - timedelta(days=1), "revenue": previous_received,
        },
        "variation_percentage": _percentage(received - previous_received, previous_received),
        "gross_revenue": gross,
        "net_revenue": net,
        "discounts": discounts,
        "discount_percentage": _percentage(discounts, gross),
        "delivery_revenue": delivery,
        "gross_profit": profit,
        "gross_margin_percentage": None if profit is None else _percentage(profit, net),
        "missing_cost_orders": missing_cost_orders,
        "unmatched_payments": unmatched_payments,
        "series": points,
        "products": sorted(products.values(), key=lambda row: (-row["quantity"], row["name"])),
        "kits": sorted(kits.values(), key=lambda row: (-row["revenue"], row["name"])),
        "payment_methods": sorted(methods.values(), key=lambda row: (-row["revenue"], row["name"])),
    }


def get_weekly_revenue(reference_date=None):
    dashboard = get_dashboard(reference_date=reference_date)
    return {
        key: dashboard[key]
        for key in ("period", "current_period", "previous_period", "variation_percentage")
    }
