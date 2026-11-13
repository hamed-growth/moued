"""Persistence models for the teams domain."""

from django.db import models
from apps.accounts.models import User


class Team(models.Model):
    """مدل تیم‌ها (گروه‌های زیرمجموعه مسجد)"""
    name = models.CharField(max_length=100, verbose_name="نام تیم")
    manager = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True,
        related_name='managed_team', verbose_name="مدیر تیم",
        limit_choices_to={'is_team_manager': True}
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'missions'
        verbose_name = "تیم"
        verbose_name_plural = "تیم‌ها"


class TeamMember(models.Model):
    """اعضای هر تیم"""
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members', verbose_name="تیم")
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='team_membership', verbose_name="کاربر")
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ عضویت")

    def __str__(self):
        return f"{self.user.username} - {self.team.name}"

    class Meta:
        app_label = 'missions'
        verbose_name = "عضو تیم"
        verbose_name_plural = "اعضای تیم"
