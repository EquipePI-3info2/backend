from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Address, User


class AddressApiTests(APITestCase):
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
        self.client.force_authenticate(self.user)
        self.list_url = reverse("addresses-list")

    def address_payload(self, **overrides):
        payload = {
            "label": "Casa",
            "street": "Rua das Flores",
            "number": "100",
            "complement": "Apto 10",
            "neighborhood": "Centro",
            "city": "Joinville",
            "state": "sc",
            "zip_code": "89200-000",
            "is_default": False,
        }
        payload.update(overrides)
        return payload

    def test_first_address_becomes_default_and_is_normalized(self):
        response = self.client.post(self.list_url, self.address_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        address = Address.objects.get(user=self.user)
        self.assertTrue(address.is_default)
        self.assertEqual(address.state, "SC")
        self.assertEqual(address.zip_code, "89200-000")

    def test_only_one_address_can_be_default(self):
        first = Address.objects.create(
            user=self.user,
            label="Casa",
            street="Rua A",
            number="1",
            neighborhood="Centro",
            city="Joinville",
            state="SC",
            zip_code="89200-000",
            is_default=True,
        )
        response = self.client.post(
            self.list_url,
            self.address_payload(label="Trabalho", street="Rua B", is_default=True),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        first.refresh_from_db()
        self.assertFalse(first.is_default)
        self.assertTrue(Address.objects.get(pk=response.data["id"]).is_default)

    def test_user_cannot_access_another_users_address(self):
        address = Address.objects.create(
            user=self.other_user,
            street="Rua de Outro Usuário",
            number="1",
            neighborhood="Centro",
            city="Joinville",
            state="SC",
            zip_code="89200-000",
            is_default=True,
        )

        response = self.client.get(reverse("addresses-detail", args=[address.pk]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_deleting_default_address_promotes_a_replacement(self):
        default_address = Address.objects.create(
            user=self.user,
            street="Rua A",
            number="1",
            neighborhood="Centro",
            city="Joinville",
            state="SC",
            zip_code="89200-000",
            is_default=True,
        )
        replacement = Address.objects.create(
            user=self.user,
            street="Rua B",
            number="2",
            neighborhood="Centro",
            city="Joinville",
            state="SC",
            zip_code="89200-001",
            is_default=False,
        )

        response = self.client.delete(
            reverse("addresses-detail", args=[default_address.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        replacement.refresh_from_db()
        self.assertTrue(replacement.is_default)
        