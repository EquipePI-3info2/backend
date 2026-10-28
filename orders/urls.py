from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import OrderViewSet, PaymentViewSet
from .views.dashboard import AdminDashboardView

router = DefaultRouter()
router.register("orders", OrderViewSet, basename="orders")
router.register("payments", PaymentViewSet, basename="payments")


urlpatterns = [
    path(
        "admin/dashboard/",
        AdminDashboardView.as_view(),
        name="admin-dashboard",
    ),
]

urlpatterns += router.urls
