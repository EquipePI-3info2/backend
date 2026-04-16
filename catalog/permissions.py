from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """
    Regra de acesso do catálogo:
      - GET, HEAD, OPTIONS → qualquer pessoa (inclusive anônimo)
      - POST, PATCH, DELETE → somente is_staff=True
    """
    message = "Apenas administradores podem modificar o catálogo."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)
