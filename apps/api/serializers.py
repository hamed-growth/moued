"""Explicit allowlist serializers: never expose password, privileges, or answer keys."""

from rest_framework import serializers

from apps.accounts.models import User
from apps.missions.models import Mission, MissionRequest
from apps.treasure.models import TreasureItem
from apps.wallet.models import PointTransaction
from apps.teams.selectors.membership import get_user_team


class MeSerializer(serializers.ModelSerializer):
    team = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", "username", "first_name", "last_name", "email",
            "total_points", "total_coins", "activity_streak", "team",
        )
        read_only_fields = fields

    def get_team(self, obj):
        team = get_user_team(obj)
        if not team:
            return None
        return {"id": team.pk, "name": team.name}


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointTransaction
        fields = ("id", "transaction_type", "title", "points", "coins", "created_at")
        read_only_fields = fields


class MissionSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    points = serializers.SerializerMethodField()
    coins = serializers.SerializerMethodField()
    available_now = serializers.SerializerMethodField()
    completed_today = serializers.SerializerMethodField()
    pending_today = serializers.SerializerMethodField()

    class Meta:
        model = Mission
        fields = (
            "id", "title", "description", "category", "points", "coins",
            "is_global", "has_time_limit", "start_time", "end_time",
            "available_now", "completed_today", "pending_today",
        )
        read_only_fields = fields

    def _rewards(self, obj):
        team = self.context.get("team")
        if team and not obj.is_global:
            for assigned in getattr(obj, "api_team_assignments", []):
                return (
                    assigned.points_override if assigned.points_override is not None else obj.points,
                    assigned.coins_override if assigned.coins_override is not None else obj.coins,
                )
        return obj.points, obj.coins

    def get_points(self, obj):
        return self._rewards(obj)[0]

    def get_coins(self, obj):
        return self._rewards(obj)[1]

    def get_category(self, obj):
        return {"id": obj.category.pk, "name": obj.category.name, "slug": obj.category.slug} if obj.category else None

    def get_available_now(self, obj):
        return obj.is_available_now()

    def get_completed_today(self, obj):
        return obj.pk in self.context.get("completed_ids", set())

    def get_pending_today(self, obj):
        return obj.pk in self.context.get("pending_ids", set())


class MissionRequestSerializer(serializers.ModelSerializer):
    mission = serializers.SerializerMethodField()

    class Meta:
        model = MissionRequest
        fields = (
            "id", "user_id", "mission", "status", "note", "admin_note", "requested_at",
            "reviewed_at", "points_awarded", "coins_awarded",
        )
        read_only_fields = fields

    def get_mission(self, obj):
        return {"id": obj.mission_id, "title": obj.mission.title}


class TreasureItemSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    available = serializers.SerializerMethodField()

    class Meta:
        model = TreasureItem
        fields = (
            "id", "name", "description", "image", "category", "price",
            "stock", "is_featured", "available",
        )
        read_only_fields = fields

    def get_category(self, obj):
        return {"id": obj.category.pk, "name": obj.category.name, "slug": obj.category.slug} if obj.category else None

    def get_available(self, obj):
        return obj.is_available()
