"""
core/validators.py

Validadores reutilizáveis para campos de upload (imagens, etc).
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

MAX_IMAGE_SIZE_MB = 5


def validate_image_size(file):
    """Garante que a imagem enviada não exceda o tamanho máximo permitido."""
    limit = MAX_IMAGE_SIZE_MB * 1024 * 1024
    if file.size > limit:
        raise ValidationError(
            _("A imagem não pode ser maior que %(max)sMB.") % {"max": MAX_IMAGE_SIZE_MB}
        )
