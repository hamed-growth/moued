"""Persistence models for the missions domain."""

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.accounts.models import User
from apps.teams.models import Team


class MissionCategory(models.Model):
    """دسته‌بندی ماموریت‌ها"""
    name = models.CharField(
        max_length=100, verbose_name="نام دسته‌بندی",
        help_text="مثلاً: عبادی، ورزشی، علمی، فرهنگی"
    )
    slug = models.SlugField(
        max_length=100, unique=True, verbose_name="شناسه (slug)",
        help_text="برای URL — مثلاً: ebadat، sport، elmi"
    )
    icon = models.CharField(
        max_length=50, default='fa-tag', verbose_name="آیکون (Font Awesome)",
        help_text="مثلاً: fa-mosque، fa-running، fa-book"
    )
    color = models.CharField(
        max_length=20, default='#d4a017', verbose_name="رنگ",
        help_text="کد رنگ HEX — مثلاً: #d4a017"
    )
    order = models.PositiveIntegerField(
        default=0, verbose_name="ترتیب نمایش",
        help_text="عدد کوچکتر = نمایش بالاتر"
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال است؟")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        app_label = 'missions'
        verbose_name = "دسته‌بندی ماموریت"
        verbose_name_plural = "دسته‌بندی‌های ماموریت"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Mission(models.Model):
    """
    تعریف کلی ماموریت‌ها در سطح سیستم.
    این ماموریت‌ها به‌تنهایی در هیچ تیمی فعال نیستند مگر:
      - در TeamMission برای آن تیم ثبت شوند، یا
      - is_global=True باشند (در همه تیم‌ها فعال).
    """
    title = models.CharField(max_length=200, verbose_name="نام ماموریت (مثلاً نماز صبح)")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    category = models.ForeignKey(
        MissionCategory, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='missions',
        verbose_name="دسته‌بندی"
    )

    # پاداش‌ها
    points = models.IntegerField(default=10, verbose_name="امتیاز")
    coins = models.IntegerField(default=0, verbose_name="سکه")

    # تنظیمات زمان
    has_time_limit = models.BooleanField(default=False, verbose_name="دارای محدودیت زمانی است؟")
    start_time = models.TimeField(null=True, blank=True, verbose_name="ساعت شروع")
    end_time = models.TimeField(null=True, blank=True, verbose_name="ساعت پایان")

    # نمایش در صفحه اصلی
    show_on_home = models.BooleanField(
        default=False,
        verbose_name="نمایش در صفحه اصلی؟",
        help_text="اگر فعال باشد، این ماموریت در صفحه خانه نمایش داده می‌شود."
    )
    home_order = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش در خانه",
        help_text="عدد کوچکتر = نمایش بالاتر"
    )

    # ماموریت مشترک و ثابت در همه تیم‌ها
    is_global = models.BooleanField(
        default=False,
        verbose_name="ماموریت مشترک/ثابت است؟",
        help_text="اگر فعال باشد، این ماموریت در همه تیم‌ها به‌صورت خودکار فعال است."
    )

    is_active = models.BooleanField(default=True, verbose_name="فعال است؟")
    created_by = models.ForeignKey(
        'User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_missions', verbose_name="سازنده"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    def clean(self):
        if self.has_time_limit:
            if not self.start_time or not self.end_time:
                raise ValidationError("برای ماموریت‌های زمان‌دار، وارد کردن ساعت شروع و پایان الزامی است.")
            if self.start_time >= self.end_time:
                raise ValidationError("ساعت شروع باید قبل از ساعت پایان باشد.")

    def is_available_now(self):
        if not self.is_active:
            return False
        if not self.has_time_limit:
            return True
        now = timezone.localtime(timezone.now()).time()
        return self.start_time <= now <= self.end_time

    def is_available_for_team(self, team):
        """
        آیا این ماموریت برای این تیم فعال است؟
        - اگر is_global باشد: بله (به شرطی که فعال باشد).
        - در غیر این صورت: باید در TeamMission برای این تیم active باشد.
        """
        if not self.is_active:
            return False
        if self.is_global:
            return True
        return self.team_assignments.filter(team=team, is_active=True).exists()

    def get_rewards_for_team(self, team=None):
        """
        برگرداندن (points, coins) با در نظر گرفتن override تیمی.
        اگر TeamMission برای این تیم مقدار override داشته باشد، از آن استفاده می‌شود.
        """
        if team is not None and not self.is_global:
            assignment = self.team_assignments.filter(team=team, is_active=True).first()
            if assignment:
                points = assignment.points_override if assignment.points_override is not None else self.points
                coins = assignment.coins_override if assignment.coins_override is not None else self.coins
                return points, coins
        return self.points, self.coins

    def __str__(self):
        return self.title

    class Meta:
        app_label = 'missions'
        verbose_name = "ماموریت"
        verbose_name_plural = "ماموریت‌ها"
        ordering = ['home_order', '-created_at']


class TeamMission(models.Model):
    """
    انتخاب ماموریت‌ها توسط هر تیم.
    مدیر هر تیم از بین ماموریت‌های سراسری، ماموریت‌های موردنظر خود را فعال می‌کند.
    (ماموریت‌های is_global نیازی به ثبت در این جدول ندارند، ولی ثبتشان مانعی ندارد.)
    """
    team = models.ForeignKey(
        Team, on_delete=models.CASCADE,
        related_name='team_missions', verbose_name="تیم"
    )
    mission = models.ForeignKey(
        Mission, on_delete=models.CASCADE,
        related_name='team_assignments', verbose_name="ماموریت"
    )
    is_active = models.BooleanField(default=True, verbose_name="در این تیم فعال است؟")

    # override اختیاری برای این تیم خاص
    points_override = models.IntegerField(
        null=True, blank=True, verbose_name="امتیاز اختصاصی این تیم",
        help_text="در صورت پر بودن، جایگزین امتیاز پیش‌فرض ماموریت می‌شود."
    )
    coins_override = models.IntegerField(
        null=True, blank=True, verbose_name="سکه اختصاصی این تیم",
        help_text="در صورت پر بودن، جایگزین سکه پیش‌فرض ماموریت می‌شود."
    )

    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش در تیم")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")

    class Meta:
        app_label = 'missions'
        verbose_name = "ماموریت تیم"
        verbose_name_plural = "ماموریت‌های تیم‌ها"
        unique_together = ('team', 'mission')
        ordering = ['order', '-created_at']

    def get_points(self):
        return self.points_override if self.points_override is not None else self.mission.points

    def get_coins(self):
        return self.coins_override if self.coins_override is not None else self.mission.coins

    def __str__(self):
        return f"{self.team.name} - {self.mission.title}"


class MissionCompletion(models.Model):
    """ثبت انجام شدن ماموریت توسط کاربر (پس از تأیید مدیر)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='completed_missions', verbose_name="کاربر")
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, verbose_name="ماموریت")
    team = models.ForeignKey(
        Team, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='mission_completions', verbose_name="تیم"
    )
    completed_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ انجام")
    points_awarded = models.IntegerField(default=0, verbose_name="امتیاز داده‌شده")
    coins_awarded = models.IntegerField(default=0, verbose_name="سکه داده‌شده")

    class Meta:
        app_label = 'missions'
        verbose_name = "انجام ماموریت"
        verbose_name_plural = "انجام ماموریت‌ها"

    def clean(self):
        today = timezone.localtime(timezone.now()).date()
        if MissionCompletion.objects.filter(
            user=self.user, mission=self.mission, completed_at__date=today
        ).exists():
            raise ValidationError("شما امروز این ماموریت را انجام داده‌اید.")

    def save(self, *args, **kwargs):
        from apps.missions.services.completion import save_mission_completion

        return save_mission_completion(self, super().save, *args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.mission.title}"


class MissionRequest(models.Model):
    """
    درخواست انجام ماموریت توسط کاربر.
    کاربر ادعا می‌کند ماموریت را انجام داده؛ مدیر تأیید یا رد می‌کند.
    در صورت تأیید، امتیاز و سکه به‌صورت خودکار داده می‌شود.
    """
    STATUS_CHOICES = (
        ('pending', 'در انتظار بررسی'),
        ('approved', 'تأیید شده'),
        ('rejected', 'رد شده'),
    )

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='mission_requests', verbose_name="کاربر"
    )
    mission = models.ForeignKey(
        Mission, on_delete=models.CASCADE,
        related_name='requests', verbose_name="ماموریت"
    )
    team = models.ForeignKey(
        Team, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='mission_requests', verbose_name="تیم",
        help_text="تیمی که کاربر در آن درخواست داده (برای اعمال override تیمی)."
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='pending',
        verbose_name="وضعیت"
    )
    note = models.TextField(
        blank=True, null=True, verbose_name="توضیح کاربر",
        help_text="توضیح اختیاری درباره نحوه انجام ماموریت."
    )
    admin_note = models.TextField(
        blank=True, null=True, verbose_name="یادداشت مدیر",
        help_text="دلیل تأیید یا رد درخواست."
    )
    requested_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان درخواست")
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان بررسی")
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_requests', verbose_name="بررسی‌کننده"
    )
    points_awarded = models.PositiveIntegerField(default=0, verbose_name="امتیاز داده‌شده")
    coins_awarded = models.PositiveIntegerField(default=0, verbose_name="سکه داده‌شده")

    class Meta:
        app_label = 'missions'
        verbose_name = "درخواست انجام ماموریت"
        verbose_name_plural = "درخواست‌های انجام ماموریت"
        ordering = ['-requested_at']

    def clean(self):
        """جلوگیری از درخواست تکراری در همان روز برای همان ماموریت"""
        if self.pk is None:
            today = timezone.localdate()
            exists = MissionRequest.objects.filter(
                user=self.user, mission=self.mission,
                requested_at__date=today,
            ).exclude(status='rejected').exists()
            if exists:
                raise ValidationError("شما امروز برای این ماموریت درخواست ثبت کرده‌اید.")

    def save(self, *, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self._state.adding:
            # A stale edit must not reopen a reviewed request or overwrite its reward metadata.
            review_fields = {'status', 'reviewed_at', 'reviewed_by', 'reviewed_by_id',
                             'points_awarded', 'coins_awarded'}
            if update_fields is None:
                update_fields = {
                    field.attname for field in self._meta.concrete_fields
                    if not field.primary_key and field.attname in self.__dict__
                    and field.attname != 'admin_note'
                }
            update_fields = set(update_fields) - review_fields
        return super().save(force_insert=force_insert, force_update=force_update,
                            using=using, update_fields=update_fields)

    def approve(self, admin_user=None, admin_note=None):
        """تأیید درخواست و اهدای امتیاز و سکه"""
        from apps.missions.services.review import approve_mission_request

        return approve_mission_request(self, admin_user=admin_user, admin_note=admin_note)

    def reject(self, admin_user=None, admin_note=None):
        """رد درخواست"""
        from apps.missions.services.review import reject_mission_request

        return reject_mission_request(self, admin_user=admin_user, admin_note=admin_note)

    def __str__(self):
        return f"{self.user.username} → {self.mission.title} ({self.get_status_display()})"
