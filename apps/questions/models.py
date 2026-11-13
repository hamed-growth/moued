"""Persistence models for the questions domain."""

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.accounts.models import User


class Question(models.Model):
    """سوالات چهارگزینه‌ای — به‌عنوان بانک سوال مشترک"""
    text = models.CharField(max_length=500, verbose_name="متن سوال")
    option_1 = models.CharField(max_length=200, verbose_name="گزینه ۱")
    option_2 = models.CharField(max_length=200, verbose_name="گزینه ۲")
    option_3 = models.CharField(max_length=200, verbose_name="گزینه ۳")
    option_4 = models.CharField(max_length=200, verbose_name="گزینه ۴")

    CORRECT_OPTIONS = [
        (1, 'گزینه ۱'),
        (2, 'گزینه ۲'),
        (3, 'گزینه ۳'),
        (4, 'گزینه ۴'),
    ]
    correct_option = models.IntegerField(choices=CORRECT_OPTIONS, verbose_name="گزینه صحیح")

    @property
    def options_dict(self):
        return {
            1: self.option_1,
            2: self.option_2,
            3: self.option_3,
            4: self.option_4,
        }

    def __str__(self):
        return self.text[:50]

    class Meta:
        app_label = 'missions'
        verbose_name = "سوال"
        verbose_name_plural = "سوالات"


class DailyQuestion(models.Model):
    """سوال روزانه"""
    DIFFICULTY_LEVELS = (
        ('easy', 'آسان'),
        ('medium', 'متوسط'),
        ('hard', 'سخت'),
    )

    question = models.ForeignKey(
        Question, on_delete=models.CASCADE,
        related_name='daily_usages', verbose_name="سوال",
        help_text="یک سوال انتخاب کنید (از بانک سوالات)."
    )
    publish_date = models.DateField(
        default=timezone.localdate, verbose_name="تاریخ انتشار",
        help_text="سوال در این تاریخ به کاربران نمایش داده می‌شود."
    )
    points = models.PositiveIntegerField(default=10, verbose_name="امتیاز پاسخ صحیح")
    difficulty = models.CharField(
        max_length=10, choices=DIFFICULTY_LEVELS, default='medium',
        verbose_name="سطح دشواری"
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال است؟")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        app_label = 'missions'
        verbose_name = "سوال روزانه"
        verbose_name_plural = "سوالات روزانه"
        ordering = ['-publish_date', '-created_at']
        unique_together = ('question', 'publish_date')

    def clean(self):
        if DailyQuestion.objects.filter(
            question=self.question, publish_date=self.publish_date
        ).exclude(pk=self.pk).exists():
            raise ValidationError("این سوال قبلاً برای این تاریخ ثبت شده است.")

    def is_today(self):
        return self.publish_date == timezone.localdate()

    def __str__(self):
        return f"{self.question.text[:40]} — {self.publish_date}"


class DailyQuestionAnswer(models.Model):
    """پاسخ کاربر به سوال روزانه"""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='daily_answers', verbose_name="کاربر"
    )
    daily_question = models.ForeignKey(
        DailyQuestion, on_delete=models.CASCADE,
        related_name='answers', verbose_name="سوال روزانه"
    )
    selected_option = models.IntegerField(verbose_name="گزینه انتخاب‌شده")
    is_correct = models.BooleanField(default=False, verbose_name="پاسخ صحیح بود؟")
    points_awarded = models.PositiveIntegerField(default=0, verbose_name="امتیاز داده‌شده")
    answered_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ پاسخ")

    class Meta:
        app_label = 'missions'
        verbose_name = "پاسخ سوال روزانه"
        verbose_name_plural = "پاسخ‌های سوالات روزانه"
        unique_together = ('user', 'daily_question')
        ordering = ['-answered_at']

    def clean(self):
        if DailyQuestionAnswer.objects.filter(
            user=self.user, daily_question=self.daily_question
        ).exclude(pk=self.pk).exists():
            raise ValidationError("شما قبلاً به این سوال پاسخ داده‌اید.")

    def save(self, *args, **kwargs):
        from apps.questions.services.rewards import save_daily_answer

        return save_daily_answer(self, super().save, *args, **kwargs)

    def __str__(self):
        status = "✓" if self.is_correct else "✗"
        return f"{self.user.username} {status} {self.daily_question}"
