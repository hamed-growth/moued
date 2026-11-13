"""Persistence models for the wallet domain."""

from django.db import models
from apps.accounts.models import User


class PointTransaction(models.Model):
    """تاریخچه تمام امتیازات و سکه‌های کسب شده"""
    TRANSACTION_TYPES = (
        ('mission', 'ماموریت'),
        ('competition', 'مسابقه'),
        ('daily_question', 'سوال روزانه'),
        ('monthly_competition', 'مسابقه ماهانه'),
        ('bonus', 'جایزه ویژه'),
        ('treasure', 'صندوق گنج'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions', verbose_name="کاربر")
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPES, verbose_name="نوع تراکنش")
    title = models.CharField(max_length=200, verbose_name="عنوان")
    points = models.IntegerField(default=0, verbose_name="امتیاز کسب شده")
    coins = models.IntegerField(default=0, verbose_name="سکه کسب شده")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ کسب")

    class Meta:
        app_label = 'missions'
        ordering = ['-created_at']
        verbose_name = "تراکنش امتیاز"
        verbose_name_plural = "تراکنش‌های امتیاز"

    def __str__(self):
        parts = []
        if self.points:
            parts.append(f"{self.points}+ امتیاز")
        if self.coins:
            parts.append(f"{self.coins}+ سکه")
        reward = " و ".join(parts) if parts else "بدون پاداش"
        return f"{self.user.username} - {self.title} ({reward})"
