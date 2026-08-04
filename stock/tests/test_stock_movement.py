from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from catalog.models import Category, Product
from stock.models import StockMovement


class StockMovementTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Cookies")
        self.product = Product.objects.create(
            category=category,
            name="Cookie de chocolate",
            price=Decimal("12.00"),
            stock=3,
        )

    def test_out_movement_deducts_stock(self):
        StockMovement.objects.create(
            product=self.product,
            movement_type=StockMovement.MovementType.OUT,
            quantity=2,
            reason="Venda",
        )

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)

    def test_out_movement_never_allows_negative_stock(self):
        with self.assertRaises(ValidationError):
            StockMovement.objects.create(
                product=self.product,
                movement_type=StockMovement.MovementType.OUT,
                quantity=4,
                reason="Venda inválida",
            )

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertFalse(StockMovement.objects.exists())

    def test_return_movement_restores_stock(self):
        StockMovement.objects.create(
            product=self.product,
            movement_type=StockMovement.MovementType.RETURN,
            quantity=2,
            reason="Cancelamento",
        )

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)

    def test_movement_is_immutable(self):
        movement = StockMovement.objects.create(
            product=self.product,
            movement_type=StockMovement.MovementType.IN,
            quantity=1,
            reason="Reposição",
        )
        movement.reason = "Alterado"

        with self.assertRaises(ValidationError):
            movement.save()