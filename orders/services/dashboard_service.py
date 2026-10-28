from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from orders.models import Payment


def _start_of_week(reference_date):
    """Retorna a segunda-feira da semana informada."""
    return reference_date - timedelta(days=reference_date.weekday())


def _start_of_day(date_value):
    """Transforma uma data no início do dia usando o fuso do projeto."""
    return timezone.make_aware(
        datetime.combine(date_value, time.min),
        timezone.get_current_timezone(),
    )


def _approved_revenue_between(start_date, end_date):
    """Soma os pagamentos aprovados dentro do período."""
    total = Payment.objects.filter(
        status=Payment.Status.APPROVED,
        paid_at__gte=_start_of_day(start_date),
        paid_at__lt=_start_of_day(end_date),
    ).aggregate(
        total=Sum("amount_paid")
    )["total"]

    return total or Decimal("0.00")


def get_weekly_revenue(reference_date=None):
    """
    Retorna o faturamento da semana atual,
    da semana anterior e a variação percentual.
    """
    reference_date = reference_date or timezone.localdate()

    current_start = _start_of_week(reference_date)
    current_end = current_start + timedelta(days=7)

    previous_start = current_start - timedelta(days=7)
    previous_end = current_start

    current_revenue = _approved_revenue_between(
        current_start,
        current_end,
    )

    previous_revenue = _approved_revenue_between(
        previous_start,
        previous_end,
    )

    if previous_revenue > 0:
        variation_percentage = (
            (current_revenue - previous_revenue)
            / previous_revenue
            * Decimal("100")
        ).quantize(Decimal("0.01"))
    elif current_revenue == 0:
        variation_percentage = Decimal("0.00")
    else:
        variation_percentage = None

    return {
        "period": "week",
        "current_period": {
            "start": current_start,
            "end": current_end - timedelta(days=1),
            "revenue": current_revenue,
        },
        "previous_period": {
            "start": previous_start,
            "end": previous_end - timedelta(days=1),
            "revenue": previous_revenue,
        },
        "variation_percentage": variation_percentage,
    }
