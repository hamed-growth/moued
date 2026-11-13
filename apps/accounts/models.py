"""Persistence models for the accounts domain."""

from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """مدل کاربر سفارشی با فیلدهای اختصاصی سیستم امتیازدهی"""
    is_team_manager = models.BooleanField(default=False, verbose_name="مدیر تیم است؟")
    total_points = models.IntegerField(default=0, verbose_name="مجموع امتیازات")
    total_coins = models.IntegerField(default=0, verbose_name="مجموع سکه‌ها")
    last_activity_date = models.DateField(null=True, blank=True, verbose_name="آخرین روز فعالیت")
    activity_streak = models.IntegerField(default=0, verbose_name="تعداد روزهای فعالیت متوالی")

    def add_points(self, points):
        """سازگاری با کدهای قبلی — فقط امتیاز"""
        self.add_rewards(points=points, coins=0)

    def add_rewards(self, points=0, coins=0):
        """افزودن امتیاز و/یا سکه به کاربر و به‌روزرسانی خودکار روزهای فعالیت"""
        from apps.wallet.services.balances import add_rewards

        add_rewards(self, points=points, coins=coins)

    def __str__(self):
        return self.username

    class Meta:
        app_label = 'missions'
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"
