from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Category, Kit, KitItem, Product
from core.models import Address, User
from orders.models import Order, OrderKitItem, Payment
from stock.models import StockMovement


class OrderApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="cliente@brookie.com",
            password="senha-segura-123",
            name="Cliente",
        )
        self.other_user = User.objects.create_user(
            email="outro@brookie.com",
            password="senha-segura-123",
            name="Outro Cliente",
        )
        self.admin = User.objects.create_user(
            email="admin@brookie.com",
            password="senha-segura-123",
            name="Administrador",
            is_staff=True,
        )
        self.address = Address.objects.create(
            user=self.user,
            label="Casa",
            street="Rua das Flores",
            number="100",
            complement="Apto 10",
            neighborhood="Centro",
            city="Joinville",
            state="SC",
            zip_code="89200-000",
            is_default=True,
        )
        self.admin_address = Address.objects.create(
            user=self.admin,
            label="Casa",
            street="Rua do Admin",
            number="1",
            neighborhood="Centro",
            city="Joinville",
            state="SC",
            zip_code="89200-001",
            is_default=True,
        )
        self.category = Category.objects.create(name="Cookies")
        self.product = Product.objects.create(
            category=self.category,
            name="Cookie clássico",
            price=Decimal("10.00"),
            cost_price=Decimal("4.00"),
            stock=5,
            is_active=True,
        )
        self.orders_url = reverse("orders-list")

    def authenticate(self, user):
        self.client.force_authenticate(user)

    def order_payload(self, **overrides):
        payload = {
            "delivery_method": Order.DeliveryMethod.DELIVERY,
            "address": self.address.pk,
            "delivery_notes": "Tocar a campainha.",
            "payment_method": Payment.Method.PIX,
            "items": [{"product": self.product.pk, "quantity": 2}],
        }
        payload.update(overrides)
        return payload

    def create_order(self, user=None, **overrides):
        self.authenticate(user or self.user)
        return self.client.post(
            self.orders_url,
            self.order_payload(**overrides),
            format="json",
        )

    def test_create_order_calculates_values_and_keeps_stock_until_payment(self):
        response = self.create_order(discount="999.00", delivery_fee="-10.00")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get(pk=response.data["id"])
        self.product.refresh_from_db()

        self.assertEqual(order.user, self.user)
        self.assertEqual(order.subtotal, Decimal("20.00"))
        self.assertEqual(order.discount, Decimal("0.00"))
        self.assertEqual(order.delivery_fee, Decimal("0.00"))
        self.assertEqual(order.total, Decimal("20.00"))
        self.assertEqual(order.delivery_address, "Rua das Flores, 100 - Apto 10 - Centro")
        self.assertEqual(order.payment.status, Payment.Status.PENDING)
        self.assertEqual(self.product.stock, 5)

    def test_delivery_requires_an_address_owned_by_user(self):
        foreign_address = Address.objects.create(
            user=self.other_user,
            street="Rua B",
            number="2",
            neighborhood="Centro",
            city="Joinville",
            state="SC",
            zip_code="89200-002",
            is_default=True,
        )

        response = self.create_order(address=foreign_address.pk)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pickup_order_has_no_delivery_address(self):
        response = self.create_order(
            delivery_method=Order.DeliveryMethod.PICKUP,
            address=None,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get(pk=response.data["id"])
        self.assertEqual(order.delivery_address, "")
        self.assertEqual(order.delivery_city, "")

    def test_customer_cannot_update_or_delete_order(self):
        response = self.create_order()
        order_id = response.data["id"]

        patch_response = self.client.patch(
            reverse("orders-detail", args=[order_id]),
            {"status": Order.Status.DELIVERED},
            format="json",
        )
        delete_response = self.client.delete(reverse("orders-detail", args=[order_id]))

        self.assertEqual(patch_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(delete_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_customer_can_cancel_pending_order(self):
        response = self.create_order()
        order = Order.objects.get(pk=response.data["id"])

        cancel_response = self.client.post(
            reverse("orders-cancel", args=[order.pk]),
            format="json",
        )

        self.assertEqual(cancel_response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        order.payment.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(order.payment.status, Payment.Status.CANCELLED)
        self.assertIsNotNone(order.cancelled_at)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)

    def test_payment_approval_confirms_order_and_deducts_stock_once(self):
        response = self.create_order()
        order = Order.objects.get(pk=response.data["id"])
        self.authenticate(self.admin)

        approve_response = self.client.patch(
            reverse("payments-detail", args=[order.payment_id]),
            {"status": Payment.Status.APPROVED, "transaction_id": "MP-123"},
            format="json",
        )

        self.assertEqual(approve_response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        order.payment.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CONFIRMED)
        self.assertEqual(order.payment.amount_paid, Decimal("20.00"))
        self.assertEqual(self.product.stock, 3)
        self.assertEqual(
            StockMovement.objects.filter(
                order=order,
                movement_type=StockMovement.MovementType.OUT,
            ).count(),
            1,
        )

        repeated_response = self.client.patch(
            reverse("payments-detail", args=[order.payment_id]),
            {"status": Payment.Status.APPROVED},
            format="json",
        )
        self.assertEqual(repeated_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)

    def test_approval_is_rolled_back_when_stock_became_insufficient(self):
        response = self.create_order(items=[{"product": self.product.pk, "quantity": 5}])
        order = Order.objects.get(pk=response.data["id"])
        Product.objects.filter(pk=self.product.pk).update(stock=1)
        self.authenticate(self.admin)

        approve_response = self.client.patch(
            reverse("payments-detail", args=[order.payment_id]),
            {"status": Payment.Status.APPROVED},
            format="json",
        )

        self.assertEqual(approve_response.status_code, status.HTTP_400_BAD_REQUEST)
        order.refresh_from_db()
        order.payment.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.payment.status, Payment.Status.PENDING)
        self.assertFalse(StockMovement.objects.filter(order=order).exists())

    def test_refund_cancels_order_and_returns_stock(self):
        response = self.create_order()
        order = Order.objects.get(pk=response.data["id"])
        self.authenticate(self.admin)
        payment_url = reverse("payments-detail", args=[order.payment_id])
        self.client.patch(
            payment_url,
            {"status": Payment.Status.APPROVED},
            format="json",
        )

        refund_response = self.client.patch(
            payment_url,
            {"status": Payment.Status.REFUNDED},
            format="json",
        )

        self.assertEqual(refund_response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(self.product.stock, 5)
        self.assertIsNotNone(order.stock_returned_at)
        self.assertEqual(
            StockMovement.objects.filter(
                order=order,
                movement_type=StockMovement.MovementType.RETURN,
            ).count(),
            1,
        )

    def test_invalid_status_transition_is_rejected(self):
        response = self.create_order()
        order = Order.objects.get(pk=response.data["id"])
        self.authenticate(self.admin)
        self.client.patch(
            reverse("payments-detail", args=[order.payment_id]),
            {"status": Payment.Status.APPROVED},
            format="json",
        )

        invalid_response = self.client.patch(
            reverse("orders-detail", args=[order.pk]),
            {"status": Order.Status.DELIVERED},
            format="json",
        )

        self.assertEqual(invalid_response.status_code, status.HTTP_400_BAD_REQUEST)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CONFIRMED)

    def test_user_only_sees_own_orders(self):
        first_response = self.create_order()
        own_order_id = first_response.data["id"]

        self.authenticate(self.other_user)
        list_response = self.client.get(self.orders_url)
        detail_response = self.client.get(
            reverse("orders-detail", args=[own_order_id])
        )

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data["results"]), 0)
        self.assertEqual(detail_response.status_code, status.HTTP_404_NOT_FOUND)


    def test_order_requires_registered_address_even_for_pickup(self):
        self.authenticate(self.other_user)
        response = self.client.post(
            self.orders_url,
            {
                "delivery_method": Order.DeliveryMethod.PICKUP,
                "payment_method": Payment.Method.PIX,
                "items": [{"product": self.product.pk, "quantity": 1}],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("address", response.data)

    def test_user_cannot_view_another_users_payment(self):
        response = self.create_order()
        order = Order.objects.get(pk=response.data["id"])
        self.authenticate(self.other_user)

        payment_response = self.client.get(
            reverse("payments-detail", args=[order.payment_id])
        )

        self.assertEqual(payment_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_approved_amount_must_match_order_total(self):
        response = self.create_order()
        order = Order.objects.get(pk=response.data["id"])
        self.authenticate(self.admin)

        approve_response = self.client.patch(
            reverse("payments-detail", args=[order.payment_id]),
            {"status": Payment.Status.APPROVED, "amount_paid": "1.00"},
            format="json",
        )

        self.assertEqual(approve_response.status_code, status.HTTP_400_BAD_REQUEST)
        order.refresh_from_db()
        order.payment.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.payment.status, Payment.Status.PENDING)
        self.assertEqual(self.product.stock, 5)

    def test_admin_me_and_latest_return_only_admin_orders(self):
        self.create_order()
        admin_payload = self.order_payload(address=self.admin_address.pk)
        self.authenticate(self.admin)
        admin_response = self.client.post(self.orders_url, admin_payload, format="json")
        admin_order_id = admin_response.data["id"]

        me_response = self.client.get(reverse("orders-me"))
        latest_response = self.client.get(reverse("orders-latest"))

        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(me_response.data["results"]), 1)
        self.assertEqual(me_response.data["results"][0]["id"], admin_order_id)
        self.assertEqual(latest_response.data["id"], admin_order_id)

    def create_test_kit(self):
        second_product = Product.objects.create(
            category=self.category,
            name="Brownie do kit",
            price=Decimal("8.00"),
            cost_price=Decimal("3.00"),
            stock=4,
            is_active=True,
        )
        kit = Kit.objects.create(
            name="Kit promocional",
            promotional_price=Decimal("25.00"),
            is_active=True,
        )
        KitItem.objects.create(kit=kit, product=self.product, quantity=2)
        KitItem.objects.create(kit=kit, product=second_product, quantity=1)
        return kit, second_product

    def test_create_order_with_kit_uses_promotional_price_and_snapshots_components(self):
        kit, second_product = self.create_test_kit()

        response = self.create_order(items=[], kits=[{"kit": kit.pk, "quantity": 1}])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get(pk=response.data["id"])
        order_kit = OrderKitItem.objects.get(order=order)
        self.assertEqual(order.subtotal, Decimal("25.00"))
        self.assertEqual(order.total, Decimal("25.00"))
        self.assertEqual(order_kit.kit_name, "Kit promocional")
        self.assertEqual(order_kit.unit_price, Decimal("25.00"))
        self.assertEqual(order_kit.components.count(), 2)
        self.product.refresh_from_db()
        second_product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)
        self.assertEqual(second_product.stock, 4)

    def test_kit_payment_approval_deducts_component_stock_and_refund_returns_it(self):
        kit, second_product = self.create_test_kit()
        response = self.create_order(items=[], kits=[{"kit": kit.pk, "quantity": 2}])
        order = Order.objects.get(pk=response.data["id"])
        self.authenticate(self.admin)
        payment_url = reverse("payments-detail", args=[order.payment_id])

        approve = self.client.patch(
            payment_url,
            {"status": Payment.Status.APPROVED},
            format="json",
        )
        self.assertEqual(approve.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        second_product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)
        self.assertEqual(second_product.stock, 2)

        refund = self.client.patch(
            payment_url,
            {"status": Payment.Status.REFUNDED},
            format="json",
        )
        self.assertEqual(refund.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        second_product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)
        self.assertEqual(second_product.stock, 4)

    def test_regular_product_and_kit_share_same_stock_validation(self):
        kit, _ = self.create_test_kit()

        response = self.create_order(
            items=[{"product": self.product.pk, "quantity": 2}],
            kits=[{"kit": kit.pk, "quantity": 2}],
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("items", response.data)
