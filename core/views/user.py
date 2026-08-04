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

    - Administradores têm acesso a todos os usuários.
    - Usuários comuns só conseguem acessar o próprio registro.
    - Criação por este endpoint é restrita a administradores.
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

    # ── /api/usuarios/me/ ────────────────────────────────────────────────────

    @extend_schema(
        methods=['GET'],
        summary='Dados do usuário autenticado',
        description='Retorna os dados do usuário autenticado.',
        request=None,
        responses={200: UserSerializer, 401: None},
    )
    @extend_schema(
        methods=['PATCH'],
        summary='Atualizar usuário autenticado',
        description='Atualiza o nome e/ou telefone do usuário autenticado.',
        request=UserUpdateSerializer,
        responses={
            200: UserSerializer,
            400: None,
            401: None,
        },
    )
    @action(
        detail=False,
        methods=['get', 'patch'],
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        """Consulta ou atualiza o usuário autenticado."""

        user = request.user

        if request.method == 'PATCH':
            serializer = UserUpdateSerializer(
                user,
                data=request.data,
                partial=True,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(
                UserSerializer(
                    user,
                    context={'request': request},
                ).data,
                status=status.HTTP_200_OK,
            )

        serializer = UserSerializer(
            user,
            context={'request': request},
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    # ── /api/usuarios/me/foto/ ───────────────────────────────────────────────

    @extend_schema(
        methods=['PATCH'],
        summary='Enviar foto de perfil',
        description='Envia ou substitui a foto de perfil do usuário.',
        request=ProfilePhotoSerializer,
        responses={
            200: UserSerializer,
            400: None,
            401: None,
        },
    )
    @extend_schema(
        methods=['DELETE'],
        summary='Remover foto de perfil',
        description='Remove a foto de perfil do usuário autenticado.',
        request=None,
        responses={
            200: UserSerializer,
            401: None,
        },
    )
    @action(
        detail=False,
        methods=['patch', 'delete'],
        url_path='me/foto',
        permission_classes=[IsAuthenticated],
        parser_classes=[MultiPartParser, FormParser],
    )
    def foto(self, request):
        """Envia, substitui ou remove a foto de perfil."""

        user = request.user

        if request.method == 'DELETE':
            if user.profile_photo:
                user.profile_photo.delete(save=False)
                user.profile_photo = None
                user.save(update_fields=['profile_photo'])

            return Response(
                UserSerializer(
                    user,
                    context={'request': request},
                ).data,
                status=status.HTTP_200_OK,
            )

        serializer = ProfilePhotoSerializer(
            user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        if user.profile_photo:
            user.profile_photo.delete(save=False)

        serializer.save()

        return Response(
            UserSerializer(
                user,
                context={'request': request},
            ).data,
            status=status.HTTP_200_OK,
        )


class UserRegistrationView(CreateAPIView):
    """Endpoint para registro de novos usuários."""

    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
