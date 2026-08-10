from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Category, Flavor, Product
from core.models import User


class AdminCatalogApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@brookie.test",
            password="Senha123!",
            name="Admin",
            is_staff=True,
        )
        self.customer = User.objects.create_user(
            email="cliente@brookie.test",
            password="Senha123!",
            name="Cliente",
        )
        self.category = Category.objects.create(name="Cookies")
        self.flavor = Flavor.objects.create(name="Chocolate")
        self.product = Product.objects.create(
            category=self.category,
            flavor=self.flavor,
            name="Cookie de chocolate",
            price=Decimal("12.00"),
            cost_price=Decimal("5.00"),
            stock=10,
        )

    def test_public_flavor_list_hides_inactive_flavors(self):
        Flavor.objects.create(name="Inativo", is_active=False)

        response = self.client.get(reverse("flavor-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item["name"] for item in response.data["results"]]
        self.assertEqual(names, ["Chocolate"])

    def test_only_admin_can_create_flavor(self):
        self.client.force_authenticate(self.customer)
        forbidden = self.client.post(
            reverse("flavor-list"),
            {"name": "Baunilha", "description": "", "is_active": True},
            format="json",
        )
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.admin)
        created = self.client.post(
            reverse("flavor-list"),
            {"name": "Baunilha", "description": "", "is_active": True},
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Flavor.objects.filter(name="Baunilha").exists())

    def test_product_search_accepts_flavor_name(self):
        response = self.client.get(reverse("product-list"), {"search": "Chocolate"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["slug"], self.product.slug)

    def test_partial_product_update_validates_existing_cost_price(self):
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            reverse("product-detail", args=[self.product.slug]),
            {"price": "4.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cost_price", response.data)
