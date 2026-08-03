from rest_framework.routers import DefaultRouter

from .views import OrderViewSet, PaymentViewSet

router = DefaultRouter()
router.register("orders", OrderViewSet, basename="orders")
router.register("payments", PaymentViewSet, basename="payments")

urlpatterns = router.urls
