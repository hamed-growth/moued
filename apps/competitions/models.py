"""Persistence models for the competitions domain."""

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from apps.accounts.models import User
from apps.questions.models import Question


class Competition(models.Model):
    """
    مدل یکپارچه مسابقات — با تمام ویژگی‌های مسابقات ماهانه،
    اما آزاد در زمان‌بندی (نه وابسته به یک ماه خاص).
    """
    STATUS_CHOICES = (
        ('draft', 'پیش‌نویس'),
        ('upcoming', 'به‌زودی'),
        ('active', 'در حال برگزاری'),
        ('finished', 'پایان‌یافته'),
        ('cancelled', 'لغو شده'),
    )

    title = models.CharField(max_length=200, verbose_name="نام مسابقه")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    start_date = models.DateTimeField(verbose_name="تاریخ و ساعت شروع")
    end_date = models.DateTimeField(verbose_name="تاریخ و ساعت پایان")

    points_per_correct = models.IntegerField(default=10, verbose_name="امتیاز هر پاسخ صحیح")
    max_questions = models.PositiveIntegerField(
        default=20, verbose_name="حداکثر تعداد سوال",
        help_text="کاربر در این مسابقه می‌تواند حداکثر به این تعداد سوال پاسخ دهد."
    )
    time_limit_minutes = models.PositiveIntegerField(
        default=30, verbose_name="محدودیت زمانی (دقیقه)",
        help_text="زمان کل مسابقه برای هر کاربر از لحظه شروع."
    )

    first_prize_points = models.PositiveIntegerField(default=500, verbose_name="جایزه نفر اول (امتیاز)")
    second_prize_points = models.PositiveIntegerField(default=300, verbose_name="جایزه نفر دوم (امتیاز)")
    third_prize_points = models.PositiveIntegerField(default=100, verbose_name="جایزه نفر سوم (امتیاز)")
    participation_bonus = models.PositiveIntegerField(
        default=20, verbose_name="جایزه شرکت (امتیاز)",
        help_text="به همه شرکت‌کنندگانی که به پایان برسند داده می‌شود."
    )

    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default='upcoming',
        verbose_name="وضعیت"
    )
    is_featured = models.BooleanField(default=False, verbose_name="مسابقه ویژه است؟")

    questions = models.ManyToManyField(
        'Question', through='CompetitionQuestion',
        related_name='competitions', verbose_name="سوالات"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        app_label = 'missions'
        verbose_name = "مسابقه"
        verbose_name_plural = "مسابقات"
        ordering = ['-start_date', '-created_at']

    def clean(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError("تاریخ شروع باید قبل از تاریخ پایان باشد.")

    def is_open(self):
        now = timezone.now()
        return self.status == 'active' and (self.start_date <= now <= self.end_date)

    def is_finished(self):
        return self.status == 'finished' or (self.end_date < timezone.now())

    def can_register(self):
        if self.status in ('finished', 'cancelled', 'draft'):
            return False
        return timezone.now() < self.end_date

    def can_play(self):
        if self.status != 'active':
            return False
        now = timezone.now()
        return self.start_date <= now <= self.end_date

    def get_leaderboard(self, limit=10):
        return self.registrations.select_related('user').order_by(
            '-total_correct', 'finished_at'
        )[:limit]

    def finalize(self):
        from apps.competitions.services.rewards import finalize_competition

        return finalize_competition(self)

    def __str__(self):
        return self.title


class CompetitionQuestion(models.Model):
    """جدول واسط بین مسابقه و سوالات با ترتیب و امتیاز اختصاصی"""
    competition = models.ForeignKey(
        Competition, on_delete=models.CASCADE,
        related_name='competition_questions', verbose_name="مسابقه"
    )
    question = models.ForeignKey(
        'Question', on_delete=models.CASCADE,
        verbose_name="سوال"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب")
    points_override = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="امتیاز اختصاصی",
        help_text="در صورت پر بودن، جایگزین امتیاز پیش‌فرض مسابقه می‌شود."
    )

    class Meta:
        app_label = 'missions'
        verbose_name = "سوال مسابقه"
        verbose_name_plural = "سوالات مسابقات"
        ordering = ['order']
        unique_together = ('competition', 'question')

    def get_points(self):
        if self.points_override is not None:
            return self.points_override
        return self.competition.points_per_correct

    def __str__(self):
        return f"{self.competition} - سوال {self.order}"


class CompetitionRegistration(models.Model):
    """ثبت‌نام و عملکرد کامل کاربر در مسابقه"""
    competition = models.ForeignKey(
        Competition, on_delete=models.CASCADE,
        related_name='registrations', verbose_name="مسابقه"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='competition_registrations', verbose_name="کاربر"
    )
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت‌نام")
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان شروع")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان پایان")

    total_correct = models.IntegerField(default=0, verbose_name="تعداد پاسخ صحیح")
    total_wrong = models.IntegerField(default=0, verbose_name="تعداد پاسخ غلط")
    total_answered = models.IntegerField(default=0, verbose_name="مجموع پاسخ‌های داده‌شده")
    score = models.IntegerField(default=0, verbose_name="امتیاز نهایی")

    is_completed = models.BooleanField(default=False, verbose_name="تمام شده؟")
    rank = models.PositiveIntegerField(null=True, blank=True, verbose_name="رتبه نهایی")

    class Meta:
        app_label = 'missions'
        verbose_name = "ثبت‌نام در مسابقه"
        verbose_name_plural = "ثبت‌نام‌های مسابقات"
        unique_together = ('competition', 'user')
        ordering = ['-score', 'finished_at']

    def start(self):
        from apps.competitions.services.participation import start_registration

        start_registration(self)

    def add_result(self, is_correct, points):
        from apps.competitions.services.participation import record_registration_result

        record_registration_result(self, is_correct, points)

    def finish(self):
        from apps.competitions.services.rewards import finish_competition_registration

        return finish_competition_registration(self)

    def is_time_expired(self):
        if not self.started_at:
            return False
        if self.competition.time_limit_minutes <= 0:
            return False
        deadline = self.started_at + timedelta(minutes=self.competition.time_limit_minutes)
        return timezone.now() > deadline

    def __str__(self):
        return f"{self.user.username} در {self.competition.title}"


class CompetitionAnswer(models.Model):
    """پاسخ کاربر به هر سوال در هر مسابقه"""
    registration = models.ForeignKey(
        CompetitionRegistration, on_delete=models.CASCADE,
        related_name='answers', verbose_name="ثبت‌نام"
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE,
        verbose_name="سوال"
    )
    selected_option = models.IntegerField(verbose_name="گزینه انتخاب‌شده")
    is_correct = models.BooleanField(default=False, verbose_name="صحیح بود؟")
    points_awarded = models.IntegerField(default=0, verbose_name="امتیاز داده‌شده")
    answered_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان پاسخ")

    class Meta:
        app_label = 'missions'
        verbose_name = "پاسخ مسابقه"
        verbose_name_plural = "پاسخ‌های مسابقات"
        unique_together = ('registration', 'question')
        ordering = ['answered_at']

    def save(self, *args, **kwargs):
        self.is_correct = (self.selected_option == self.question.correct_option)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.registration.user.username} - {self.question.text[:30]}"
