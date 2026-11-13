from django.contrib import admin
from apps.missions.models import TeamMission
from apps.teams.models import Team, TeamMember


class TeamMissionInline(admin.TabularInline):
    """فعال‌سازی ماموریت‌ها برای یک تیم از همان صفحه تیم"""
    model = TeamMission
    extra = 1
    autocomplete_fields = ('mission',)
    fields = ('mission', 'is_active', 'points_override', 'coins_override', 'order')
    ordering = ('order',)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'manager', 'created_at', 'members_count', 'missions_count')
    search_fields = ('name', 'manager__username')
    inlines = [TeamMissionInline]

    @admin.display(description="تعداد اعضا")
    def members_count(self, obj):
        return obj.members.count()

    @admin.display(description="ماموریت‌های فعال")
    def missions_count(self, obj):
        return obj.team_missions.filter(is_active=True).count()


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'team', 'joined_at')
    list_filter = ('team',)
    search_fields = ('user__username', 'team__name')
    autocomplete_fields = ('team', 'user')
