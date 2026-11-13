"""Read-only HTTP boundary. All sensitive queries are scoped to request.user."""

from django.db.models import Prefetch
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.missions.models import MissionCompletion, MissionRequest, TeamMission
from apps.missions.selectors.eligibility import get_user_available_missions
from apps.teams.selectors.membership import get_user_team
from apps.treasure.models import TreasureItem
from apps.wallet.models import PointTransaction
from .serializers import (
    MeSerializer, MissionRequestSerializer, MissionSerializer,
    TransactionSerializer, TreasureItemSerializer,
)


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(request.user).data)


class WalletView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({"total_points": user.total_points, "total_coins": user.total_coins})


class MyTransactionList(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TransactionSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return PointTransaction.objects.filter(user=self.request.user).order_by("-created_at", "-pk")


class MyMissionRequestList(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MissionRequestSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return (MissionRequest.objects.filter(user=self.request.user)
                .select_related("mission").order_by("-requested_at", "-pk"))


class MissionList(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MissionSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        team = get_user_team(self.request.user)
        qs = (get_user_available_missions(self.request.user)
              .select_related("category").order_by("home_order", "-created_at", "-pk"))
        if team is not None:
            qs = qs.prefetch_related(Prefetch(
                "team_assignments",
                queryset=TeamMission.objects.filter(team_id=team.pk),
                to_attr="api_team_assignments",
            ))
        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        today = timezone.localdate()
        context["team"] = get_user_team(user)
        context["completed_ids"] = set(
            MissionCompletion.objects.filter(
                user=user, completed_at__date=today,
            ).values_list("mission_id", flat=True)
        )
        context["pending_ids"] = set(
            MissionRequest.objects.filter(
                user=user, requested_at__date=today,
            ).exclude(status="rejected").values_list("mission_id", flat=True)
        )
        return context


class TreasureCatalogList(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TreasureItemSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = (TreasureItem.objects.filter(is_active=True)
              .select_related("category").order_by("-is_featured", "-created_at", "-pk"))
        slug = self.request.query_params.get("category")
        if slug:
            qs = qs.filter(category__slug=slug, category__is_active=True)
        return qs
