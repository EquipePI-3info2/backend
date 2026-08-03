from django.db import transaction
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from core.models import Address
from core.serializers import AddressSerializer


@extend_schema_view(
    list=extend_schema(summary="Listar endereços do usuário"),
    retrieve=extend_schema(summary="Detalhar endereço"),
    create=extend_schema(summary="Cadastrar endereço"),
    partial_update=extend_schema(summary="Editar endereço"),
    destroy=extend_schema(summary="Excluir endereço"),
)
class AddressViewSet(viewsets.ModelViewSet):
    # Queryset base necessário para o drf-spectacular identificar o model.
    queryset = Address.objects.none()
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Address.objects.none()

        queryset = Address.objects.select_related("user").order_by(
            "-is_default",
            "-created_at",
        )
        return queryset.filter(user=self.request.user)

    @transaction.atomic
    def perform_destroy(self, instance):
        user = instance.user
        was_default = instance.is_default
        instance.delete()

        if was_default:
            replacement = Address.objects.filter(user=user).order_by("-created_at").first()
            if replacement is not None:
                replacement.is_default = True
                replacement.save(update_fields=["is_default", "updated_at"])
