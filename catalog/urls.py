from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, FlavorViewSet, KitViewSet, ProductViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("flavors", FlavorViewSet, basename="flavor")
router.register("kits", KitViewSet, basename="kit")
router.register("products", ProductViewSet, basename="product")

urlpatterns = router.urls
