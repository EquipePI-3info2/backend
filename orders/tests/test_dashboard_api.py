from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from catalog.models import Category, Kit, KitItem, Product
from core.models import User
from orders.models import Order, Payment
from orders.services.order_service import create_order, update_payment_status


class DashboardApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = User.objects.create_user(email="cliente@brookie.test", name="Cliente")
        cls.admin = User.objects.create_user(
            email="admin@brookie.test", name="Admin", is_staff=True
        )
        category = Category.objects.create(name="Cookies")
        cls.product = Product.objects.create(
            category=category, name="Cookie", price=Decimal("10.00"),
            cost_price=Decimal("4.00"), stock=100,
        )
        cls.kit = Kit.objects.create(name="Dupla", promotional_price=Decimal("16.00"))
        KitItem.objects.create(kit=cls.kit, product=cls.product, quantity=2)

    def setUp(self):
        self.url = reverse("admin-dashboard")

    def test_dashboard_requires_staff_and_valid_period(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)
        self.client.force_authenticate(self.customer)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get(self.url, {"period": "invalid"}).status_code, 400)

    def test_weekly_dashboard_uses_approved_sales_and_historical_cost(self):
        order = create_order(
            user=self.customer, address=None, delivery_method=Order.DeliveryMethod.PICKUP,
            delivery_notes="", payment_method=Payment.Method.PIX,
            items=[{"product": self.product, "quantity": 2}],
            kits=[{"kit": self.kit, "quantity": 1}],
        )
        order.discount = Decimal("3.60")
        order.delivery_fee = Decimal("5.00")
        order.save()
        with patch("orders.services.order_service.timezone.now", return_value=self.at(11, 1)):
            update_payment_status(payment=order.payment, new_status=Payment.Status.APPROVED, actor=self.admin)
        Product.objects.filter(pk=self.product.pk).update(cost_price=Decimal("8.00"))
        Payment.objects.create(
            method=Payment.Method.CASH, status=Payment.Status.APPROVED,
            amount_paid=Decimal("18.70"), paid_at=self.at(8, 23),
        )
        Payment.objects.create(
            method=Payment.Method.PIX, status=Payment.Status.REFUNDED,
            amount_paid=Decimal("50.00"), paid_at=self.at(11, 10),
        )
        self.client.force_authenticate(self.admin)

        with patch("orders.services.dashboard_service.timezone.localdate", side_effect=self.local_date):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
            data = response.data
            self.assertEqual(data["current_period"]["revenue"], Decimal("37.40"))
            self.assertEqual(data["previous_period"]["revenue"], Decimal("18.70"))
            self.assertEqual(data["variation_percentage"], Decimal("100.00"))
            self.assertEqual(data["gross_revenue"], Decimal("36.00"))
            self.assertEqual(data["net_revenue"], Decimal("32.40"))
            self.assertEqual(data["discount_percentage"], Decimal("10.00"))
            self.assertEqual(data["delivery_revenue"], Decimal("5.00"))
            self.assertEqual(data["gross_profit"], Decimal("16.40"))
            self.assertEqual(data["gross_margin_percentage"], Decimal("50.62"))
            self.assertEqual(data["products"][0]["quantity"], 4)
            self.assertEqual(data["products"][0]["revenue"], Decimal("20.00"))
            self.assertEqual(data["kits"][0]["revenue"], Decimal("16.00"))
            self.assertEqual(data["payment_methods"][0]["revenue"], Decimal("37.40"))
            self.assertEqual(data["series"][-1], {"date": date(2026, 11, 11), "revenue": Decimal("37.40")})

            order.items.update(unit_cost=None)
            data = self.client.get(self.url).data
            self.assertEqual(data["missing_cost_orders"], 1)
            self.assertIsNone(data["gross_profit"])
            self.assertIsNone(data["gross_margin_percentage"])

    @staticmethod
    def at(day, hour):
        return timezone.make_aware(datetime(2026, 11, day, hour))

    @staticmethod
    def local_date(value=None):
        return timezone.localtime(value).date() if value else date(2026, 11, 11)
