"""
core/models/user.py

Usuário customizado. Login via e-mail.

Ajustes vs versão anterior:
  - name: blank=True, null=True → blank=False, null=False (campo obrigatório)
  - telefone adicionado (usado no checkout e no painel admin)
  - created_at / updated_at adicionados (rastreabilidade)
  - profile_photo adicionado (foto de perfil — admin e cliente)
"""
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.validators import validate_image_size


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address.")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """Usuário do sistema. Login via e-mail."""

    email = models.EmailField(
        _("e-mail"),
        max_length=255,
        unique=True,
        help_text=_("Endereço de e-mail. Usado como login."),
    )
    name = models.CharField(
        _("nome completo"),
        max_length=255,
        help_text=_("Nome completo do usuário."),
    )
    telefone = models.CharField(
        _("telefone"),
        max_length=20,
        blank=True,
        default="",
        help_text=_("Telefone para contato (opcional). Ex: (47) 99999-0000."),
    )
    profile_photo = models.ImageField(
        _("foto de perfil"),
        upload_to="users/avatars/",
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp"]),
            validate_image_size,
        ],
        help_text=_(
            "Foto de perfil do usuário (opcional). "
            "Formatos aceitos: JPG, PNG, WEBP. Máx. 5MB."
        ),
    )
    is_active = models.BooleanField(
        _("ativo"),
        default=True,
        help_text=_("Indica que este usuário está ativo."),
    )
    is_staff = models.BooleanField(
        _("equipe"),
        default=False,
        help_text=_("Indica que este usuário pode acessar o painel admin."),
    )
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("atualizado em"), auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} <{self.email}>"
