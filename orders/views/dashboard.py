from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.services.dashboard_service import PERIODS, get_dashboard


class AdminDashboardView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Resumo financeiro do painel administrativo",
        parameters=[OpenApiParameter("period", str, enum=PERIODS, default="week")],
        responses={200: dict},
    )
    def get(self, request):
        period = request.query_params.get("period", "week")
        if period not in PERIODS:
            raise ValidationError({"period": "Selecione day, week, month ou year."})
        return Response(get_dashboard(period))
