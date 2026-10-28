from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.services.dashboard_service import get_weekly_revenue


class AdminDashboardView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Resumo financeiro semanal do dashboard administrativo"
    )
    def get(self, request):
        return Response(get_weekly_revenue())
