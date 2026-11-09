from django.db import models, transaction
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Case, Sum, Count, Q, F, Value, When
from datetime import timedelta


# =====================================================================
# ۱. بخش کاربران و تیم‌ها
# =====================================================================

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
        if points:
            self.total_points += points
        if coins:
            self.total_coins += coins

        today = timezone.now().date()
        if self.last_activity_date != today:
            if self.last_activity_date == today - timedelta(days=1):
                self.activity_streak += 1
            else:
                self.activity_streak = 1
            self.last_activity_date = today

        self.save()

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"


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
        verbose_name = "عضو تیم"
        verbose_name_plural = "اعضای تیم"


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


# =====================================================================
# ۲. بخش ماموریت‌ها
# =====================================================================

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
        verbose_name = "انجام ماموریت"
        verbose_name_plural = "انجام ماموریت‌ها"

    def clean(self):
        today = timezone.localtime(timezone.now()).date()
        if MissionCompletion.objects.filter(
            user=self.user, mission=self.mission, completed_at__date=today
        ).exists():
            raise ValidationError("شما امروز این ماموریت را انجام داده‌اید.")

    def save(self, *args, **kwargs):
        if self.pk is not None:
            return super().save(*args, **kwargs)

        with transaction.atomic():
            self.points_awarded, self.coins_awarded = self.mission.get_rewards_for_team(self.team)
            super().save(*args, **kwargs)
            today = timezone.now().date()
            User.objects.filter(pk=self.user_id).update(
                total_points=F('total_points') + self.points_awarded,
                total_coins=F('total_coins') + self.coins_awarded,
                last_activity_date=today,
                activity_streak=Case(
                    When(last_activity_date=today, then=F('activity_streak')),
                    When(last_activity_date=today - timedelta(days=1), then=F('activity_streak') + 1),
                    default=Value(1),
                ),
            )
            PointTransaction.objects.create(
                user_id=self.user_id,
                transaction_type='mission',
                title=f"ماموریت: {self.mission.title}",
                points=self.points_awarded,
                coins=self.coins_awarded,
            )

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
        from .services.mission_review import approve_mission_request

        return approve_mission_request(self, admin_user=admin_user, admin_note=admin_note)

    def reject(self, admin_user=None, admin_note=None):
        """رد درخواست"""
        from .services.mission_review import reject_mission_request

        return reject_mission_request(self, admin_user=admin_user, admin_note=admin_note)

    def __str__(self):
        return f"{self.user.username} → {self.mission.title} ({self.get_status_display()})"


# =====================================================================
# ۳. بخش مسابقات (ادغام‌شده با مسابقات ماهانه)
# =====================================================================

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
        from .services.competitions import finalize_competition

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
        verbose_name = "ثبت‌نام در مسابقه"
        verbose_name_plural = "ثبت‌نام‌های مسابقات"
        unique_together = ('competition', 'user')
        ordering = ['-score', 'finished_at']

    def start(self):
        if not self.started_at:
            self.started_at = timezone.now()
            self.save(update_fields=['started_at'])

    def add_result(self, is_correct, points):
        self.total_answered += 1
        if is_correct:
            self.total_correct += 1
            self.score += points
        else:
            self.total_wrong += 1
        self.save(update_fields=['total_answered', 'total_correct', 'total_wrong', 'score'])

    def finish(self):
        from .services.competitions import finish_competition_registration

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


# =====================================================================
# ۴. بخش سوالات (بانک سوال مشترک)
# =====================================================================

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
        verbose_name = "سوال"
        verbose_name_plural = "سوالات"


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
        verbose_name = "پاسخ مسابقه"
        verbose_name_plural = "پاسخ‌های مسابقات"
        unique_together = ('registration', 'question')
        ordering = ['answered_at']

    def save(self, *args, **kwargs):
        self.is_correct = (self.selected_option == self.question.correct_option)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.registration.user.username} - {self.question.text[:30]}"


# =====================================================================
# ۵. بخش سوالات روزانه
# =====================================================================

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
        is_new = self.pk is None
        correct_option = self.daily_question.question.correct_option

        self.is_correct = (self.selected_option == correct_option)

        if self.is_correct:
            self.points_awarded = self.daily_question.points
        else:
            self.points_awarded = 0

        super().save(*args, **kwargs)

        if is_new:
            if self.is_correct:
                self.user.add_points(self.points_awarded)
                PointTransaction.objects.create(
                    user=self.user,
                    transaction_type='daily_question',
                    title=f"پاسخ صحیح به سوال روزانه: {self.daily_question.question.text[:40]}",
                    points=self.points_awarded
                )
            else:
                self.user.add_points(0)

    def __str__(self):
        status = "✓" if self.is_correct else "✗"
        return f"{self.user.username} {status} {self.daily_question}"


# =====================================================================
# ۶. بخش صندوق گنج (فروشگاه امتیازی)
# =====================================================================

class TreasureCategory(models.Model):
    """دسته‌بندی آیتم‌های صندوق گنج"""
    name = models.CharField(
        max_length=80, verbose_name="نام دسته‌بندی",
        help_text="مثلاً: کارت هدیه، کتاب، خوراکی"
    )
    slug = models.SlugField(
        max_length=80, unique=True, verbose_name="شناسه (slug)",
        help_text="برای URL — مثلاً: gift-card، book"
    )
    icon = models.CharField(
        max_length=50, default='fa-tag', verbose_name="آیکون (Font Awesome)",
        help_text="مثلاً: fa-gift، fa-book، fa-utensils"
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
        verbose_name = "دسته‌بندی صندوق گنج"
        verbose_name_plural = "دسته‌بندی‌های صندوق گنج"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class TreasureItem(models.Model):
    """آیتم قابل خرید در صندوق گنج (فروشگاه امتیازی)"""
    category = models.ForeignKey(
        TreasureCategory, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='items',
        verbose_name="دسته‌بندی"
    )
    name = models.CharField(max_length=150, verbose_name="نام آیتم")
    description = models.TextField(
        blank=True, null=True, verbose_name="توضیحات",
        help_text="توضیح کوتاه درباره آیتم."
    )
    image = models.ImageField(
        upload_to='treasure/items/', verbose_name="تصویر آیتم",
        help_text="تصویر آیتم را آپلود کنید."
    )
    price = models.PositiveIntegerField(
        default=100, verbose_name="قیمت (امتیاز)",
        help_text="امتیاز لازم برای خرید این آیتم."
    )
    stock = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="موجودی",
        help_text="تعداد قابل خرید. اگر خالی باشد = نامحدود."
    )
    is_featured = models.BooleanField(
        default=False, verbose_name="آیتم ویژه",
        help_text="آیتم‌های ویژه در بالای فروشگاه نمایش داده می‌شوند."
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال است؟")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        verbose_name = "آیتم صندوق گنج"
        verbose_name_plural = "آیتم‌های صندوق گنج"
        ordering = ['-is_featured', '-created_at']

    def is_available(self):
        if not self.is_active:
            return False
        if self.stock is None:
            return True
        return self.stock > 0

    def __str__(self):
        return f"{self.name} ({self.price} امتیاز)"


class TreasurePurchase(models.Model):
    """تاریخچه خریدهای کاربر از صندوق گنج"""
    STATUS_CHOICES = (
        ('pending', 'در انتظار تحویل'),
        ('delivered', 'تحویل داده شده'),
        ('cancelled', 'لغو شده'),
    )

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='treasure_purchases', verbose_name="کاربر"
    )
    item = models.ForeignKey(
        TreasureItem, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='purchases',
        verbose_name="آیتم"
    )
    item_name = models.CharField(
        max_length=150, verbose_name="نام آیتم (در زمان خرید)",
        help_text="نام آیتم در زمان خرید — در صورت حذف آیتم، این باقی می‌ماند."
    )
    item_price = models.PositiveIntegerField(
        verbose_name="قیمت (در زمان خرید)"
    )
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default='pending',
        verbose_name="وضعیت"
    )
    admin_note = models.TextField(
        blank=True, null=True, verbose_name="یادداشت مدیر",
        help_text="مثلاً توضیح تحویل یا دلیل لغو."
    )
    purchased_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان خرید")
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان تحویل")

    class Meta:
        verbose_name = "خرید از صندوق گنج"
        verbose_name_plural = "خریدهای صندوق گنج"
        ordering = ['-purchased_at']

    def deliver(self, admin_note=None):
        if self.status == 'delivered':
            return False
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        if admin_note:
            self.admin_note = admin_note
        self.save()
        return True

    def __str__(self):
        return f"{self.user.username} → {self.item_name} ({self.item_price} امتیاز)"
