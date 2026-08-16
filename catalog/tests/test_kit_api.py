import json
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Category, Kit, KitItem, Product
from core.models import User


class KitApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin-kit@brookie.test",
            password="Senha123!",
            name="Admin",
            is_staff=True,
        )
        self.customer = User.objects.create_user(
            email="cliente-kit@brookie.test",
            password="Senha123!",
            name="Cliente",
        )
        self.category = Category.objects.create(name="Cookies")
        self.cookie = Product.objects.create(
            category=self.category,
            name="Cookie Chocolate",
            price=Decimal("10.00"),
            stock=10,
            is_active=True,
        )
        self.brownie = Product.objects.create(
            category=self.category,
            name="Brownie",
            price=Decimal("8.00"),
            stock=6,
            is_active=True,
        )
        self.kit = Kit.objects.create(
            name="Kit Dupla",
            promotional_price=Decimal("24.00"),
        )
        KitItem.objects.create(kit=self.kit, product=self.cookie, quantity=2)
        KitItem.objects.create(kit=self.kit, product=self.brownie, quantity=1)

    def test_public_kit_returns_prices_composition_and_available_stock(self):
        response = self.client.get(reverse("kit-detail", args=[self.kit.slug]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data["regular_price"]), Decimal("28.00"))
        self.assertEqual(Decimal(response.data["promotional_price"]), Decimal("24.00"))
        self.assertEqual(Decimal(response.data["savings"]), Decimal("4.00"))
        self.assertEqual(response.data["available_stock"], 5)
        self.assertTrue(response.data["is_in_stock"])
        self.assertEqual(len(response.data["items"]), 2)

    def test_only_admin_can_create_kit(self):
        payload = {
            "name": "Kit Promo",
            "description": "",
            "promotional_price": "15.00",
            "is_active": True,
            "is_featured": True,
            "items": [
                {"product": self.cookie.pk, "quantity": 1},
                {"product": self.brownie.pk, "quantity": 1},
            ],
        }

        self.client.force_authenticate(self.customer)
        forbidden = self.client.post(reverse("kit-list"), payload, format="json")
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.admin)
        created = self.client.post(reverse("kit-list"), payload, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        kit = Kit.objects.get(name="Kit Promo")
        self.assertEqual(kit.items.count(), 2)

    def test_promotional_price_must_be_lower_than_regular_price(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse("kit-list"),
            {
                "name": "Kit sem desconto",
                "promotional_price": "18.00",
                "items": [
                    {"product": self.cookie.pk, "quantity": 1},
                    {"product": self.brownie.pk, "quantity": 1},
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("promotional_price", response.data)

    def test_admin_can_create_kit_using_multipart_items_json(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse("kit-list"),
            {
                "name": "Kit Multipart",
                "promotional_price": "16.00",
                "is_active": "true",
                "is_featured": "false",
                "items_json": json.dumps(
                    [
                        {"product": self.cookie.pk, "quantity": 1},
                        {"product": self.brownie.pk, "quantity": 1},
                    ]
                ),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Kit.objects.filter(name="Kit Multipart").exists())
