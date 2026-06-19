from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.models import User
from core.permissions import IsSelfOrAdmin
from core.serializers import (
    ProfilePhotoSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


class UserViewSet(ModelViewSet):
    """
    CRUD de usuários.

    - Administradores (is_staff=True) têm acesso a todos os usuários.
    - Usuários comuns só conseguem ver/editar/excluir o próprio registro.
    - Criação via este endpoint é restrita a admins
      (cadastro público continua em /api/registro/).
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsSelfOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return User.objects.all().order_by('id')
        return User.objects.filter(pk=user.pk).order_by('id')

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()

    # ── /me/ ─────────────────────────────────────────────────────────────────

    @extend_schema(
        summary="Dados do usuário autenticado",
        description="GET retorna os dados; PATCH atualiza nome e telefone.",
        responses={200: UserSerializer, 401: None},
    )
    @action(
        detail=False,
        methods=['get', 'patch'],
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        """GET → dados do usuário. PATCH → atualiza nome e/ou telefone."""
        user = request.user

        if request.method == 'PATCH':
            serializer = UserUpdateSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            # Retorna o UserSerializer completo (com URL da foto, created_at, etc.)
            return Response(
                UserSerializer(user, context={'request': request}).data,
                status=status.HTTP_200_OK,
            )

        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    # ── /me/foto/ ─────────────────────────────────────────────────────────────

    @extend_schema(
        summary="Upload da foto de perfil",
        description="PATCH envia nova foto; DELETE remove a foto atual.",
        request=ProfilePhotoSerializer,
        responses={200: UserSerializer, 400: None},
    )
    @action(
        detail=False,
        methods=['patch'],
        url_path='me/foto',
        permission_classes=[IsAuthenticated],
        parser_classes=[MultiPartParser, FormParser],
    )
    def foto(self, request):
        """Upload ou substituição da foto de perfil do usuário autenticado."""
        user = request.user
        serializer = ProfilePhotoSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Remove a foto antiga do storage (Cloudinary ou disco) antes de salvar
        if user.profile_photo:
            user.profile_photo.delete(save=False)

        serializer.save()
        return Response(
            UserSerializer(user, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )

    @foto.mapping.delete
    def remover_foto(self, request):
        """Remove a foto de perfil do usuário autenticado."""
        user = request.user
        if user.profile_photo:
            user.profile_photo.delete(save=False)
            user.profile_photo = None
            user.save(update_fields=['profile_photo'])
        return Response(
            UserSerializer(user, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )


class UserRegistrationView(CreateAPIView):
    """Endpoint para registro de novos usuários."""

    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
