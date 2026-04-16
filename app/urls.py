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

from core.views import UserRegistrationView, UserViewSet

router = DefaultRouter()
router.register(r'usuarios', UserViewSet, basename='usuarios')

urlpatterns = [
    path('admin/', admin.site.urls),

    # ── OpenAPI 3 / Swagger ──────────────────────────────────────
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/doc/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # ── Autenticação JWT ─────────────────────────────────────────
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # ── Usuários (core) ──────────────────────────────────────────
    path('api/registro/', UserRegistrationView.as_view(), name='user_registration'),
    path('api/', include(router.urls)),

    # ── Catálogo (catalog) ← NOVO ────────────────────────────────
    # Gera automaticamente:
    #   /api/products/
    #   /api/products/{slug}/
    #   /api/categories/
    #   /api/categories/{slug}/
    #   /api/categories/{slug}/products/
    path('api/', include('catalog.urls')),
]

# Serve arquivos de mídia localmente no modo desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)