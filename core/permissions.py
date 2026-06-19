"""
core/permissions.py
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsSelfOrAdmin(BasePermission):
    """
    - Leitura (GET/HEAD/OPTIONS): liberado para o próprio usuário autenticado
      (o queryset do ViewSet já restringe não-admins ao próprio registro).
    - Escrita (PUT/PATCH/DELETE): somente o próprio usuário ou um admin
      (is_staff=True) pode alterar/excluir.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user.is_staff or obj == request.user)
