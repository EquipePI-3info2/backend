from django.conf import settings
from django.db import models
from django.db.models import Q


class Address(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses",
        verbose_name="Usuário",
    )
    label = models.CharField(
        "Identificação",
        max_length=50,
        blank=True,
        help_text="Ex.: Casa, Trabalho.",
    )
    street = models.CharField("Logradouro", max_length=200)
    number = models.CharField("Número", max_length=20)
    complement = models.CharField("Complemento", max_length=100, blank=True)
    neighborhood = models.CharField("Bairro", max_length=100)
    city = models.CharField("Cidade", max_length=100)
    state = models.CharField("Estado (UF)", max_length=2)
    zip_code = models.CharField("CEP", max_length=9)
    is_default = models.BooleanField("Endereço padrão", default=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Endereço"
        verbose_name_plural = "Endereços"
        ordering = ["-is_default", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(is_default=True),
                name="unique_default_address_per_user",
            )
        ]

    def __str__(self):
        return f"{self.street}, {self.number} - {self.city}/{self.state}"

    @property
    def full_street(self):
        value = f"{self.street}, {self.number}"
        if self.complement:
            value = f"{value} - {self.complement}"
        if self.neighborhood:
            value = f"{value} - {self.neighborhood}"
        return value
