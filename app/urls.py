from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from catalog.views import CategoryViewSet, ProductViewSet
from core.views import UserRegistrationView, UserViewSet

# ── Router único — todos os ViewSets registrados aqui ────────────────────────
# Usar UM único DefaultRouter evita o problema do API Root incompleto.
# Antes havia dois routers separados (core e catalog), e o /api/ só exibia
# o que estava no router do core. Agora tudo aparece na API Root.
router = DefaultRouter()
router.register(r"usuarios", UserViewSet, basename="usuarios")
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"products", ProductViewSet, basename="product")

urlpatterns = [
    path("admin/", admin.site.urls),
    # ── OpenAPI 3 / Swagger ──────────────────────────────────────────────────
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/doc/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # ── Autenticação JWT ─────────────────────────────────────────────────────
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # ── Registro de usuário ──────────────────────────────────────────────────
    path("api/registro/", UserRegistrationView.as_view(), name="user_registration"),
    # ── Todas as rotas dos ViewSets via router único ─────────────────────────
    # GET        /api/                            → API Root
    # GET/POST   /api/usuarios/
    # GET/PATCH  /api/usuarios/{id}/
    # GET/POST   /api/categories/
    # GET/PATCH  /api/categories/{slug}/
    # GET        /api/categories/{slug}/products/
    # GET/POST   /api/products/
    # GET/PATCH  /api/products/{slug}/
    path("api/", include(router.urls)),
]

# ── Arquivos de mídia em desenvolvimento ────────────────────────────────────
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
