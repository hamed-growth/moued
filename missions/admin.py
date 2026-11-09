from django import forms
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin

from .models import *


# =====================================================================
# 🎨 دسته‌بندی سایدبار ادمین
# =====================================================================

ADMIN_GROUPS = [
    {
        'key': 'users',
        'name': 'اطلاعات کاربران و گروه‌ها',
        'icon': 'fa-users',
        'color': '#4338ca',
        'models': ['User', 'Group', 'Team', 'TeamMember', 'PointTransaction'],
    },
    {
        'key': 'questions',
        'name': 'سوالات',
        'icon': 'fa-circle-question',
        'color': '#0284c7',
        'models': ['Question', 'DailyQuestion', 'DailyQuestionAnswer'],
    },
    {
        'key': 'missions',
        'name': 'ماموریت‌ها',
        'icon': 'fa-list-check',
        'color': '#059669',
        'models': [
            'MissionCategory', 'Mission', 'TeamMission',
            'MissionRequest', 'MissionCompletion',
        ],
    },
    {
        'key': 'competitions',
        'name': 'مسابقات',
        'icon': 'fa-trophy',
        'color': '#d4a017',
        'models': [
            'Competition', 'CompetitionQuestion',
            'CompetitionRegistration', 'CompetitionAnswer',
        ],
    },
    {
        'key': 'treasure',
        'name': 'جوایز و صندوق گنج',
        'icon': 'fa-gift',
        'color': '#dc2626',
        'models': ['TreasureCategory', 'TreasureItem', 'TreasurePurchase'],
    },
]


def get_grouped_app_list(original_app_list):
    """مدل‌ها را در گروه‌های سفارشی مرتب می‌کند"""
    all_models = {}
    for app in original_app_list:
        for model in app['models']:
            all_models[model['object_name']] = model

    grouped_app_list = []

    for group in ADMIN_GROUPS:
        group_models = []
        for model_name in group['models']:
            if model_name in all_models:
                group_models.append(all_models[model_name])

        if group_models:
            grouped_app_list.append({
                'name': group['name'],
                'app_label': group['key'],
                'app_url': '',
                'has_module_perms': True,
                'models': group_models,
                'icon': group['icon'],
                'color': group['color'],
            })

    used_models = set()
    for group in ADMIN_GROUPS:
        used_models.update(group['models'])

    remaining = []
    for model_name, model in all_models.items():
        if model_name not in used_models:
            remaining.append(model)

    if remaining:
        grouped_app_list.append({
            'name': 'سایر',
            'app_label': 'other',
            'app_url': '',
            'has_module_perms': True,
            'models': remaining,
            'icon': 'fa-cube',
            'color': '#78716c',
        })

    return grouped_app_list


# =====================================================================
# 🔧 جایگزینی متد get_app_list در AdminSite
# =====================================================================

_original_get_app_list = admin.AdminSite.get_app_list


def _custom_get_app_list(self, request, app_label=None):
    original_list = _original_get_app_list(self, request, app_label)
    if app_label is None:
        return get_grouped_app_list(original_list)
    return original_list


admin.AdminSite.get_app_list = _custom_get_app_list


# =====================================================================
# 👥 گروه‌های کاربری (پیش‌فرض Django)
# =====================================================================

try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass


class SystemPrivilegeFields:
    """Keep ordinary admin edits separate from system privilege changes."""

    privilege_fields = ()

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if request.user.is_superuser:
            return fields
        return (*fields, *self.privilege_fields)

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        if (
            request.method == "POST"
            and not request.user.is_superuser
            and any(field in request.POST for field in self.privilege_fields)
        ):
            raise PermissionDenied
        return super().changeform_view(request, object_id, form_url, extra_context)


@admin.register(Group)
class GroupAdmin(SystemPrivilegeFields, BaseGroupAdmin):
    """گروه‌های کاربری — برای مدیریت دسترسی‌ها"""
    list_display = ('name', 'permissions_count', 'users_count')
    search_fields = ('name',)
    filter_horizontal = ('permissions',)
    privilege_fields = ('permissions',)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser and super().has_delete_permission(request, obj)

    @admin.display(description="تعداد دسترسی")
    def permissions_count(self, obj):
        return obj.permissions.count()

    @admin.display(description="تعداد کاربر")
    def users_count(self, obj):
        return obj.user_set.count()


# =====================================================================
# کاربران و تیم‌ها
# =====================================================================

@admin.register(User)
class UserAdmin(SystemPrivilegeFields, admin.ModelAdmin):
    privilege_fields = ('is_staff', 'is_superuser', 'groups', 'user_permissions')
    list_display = (
        'username', 'total_points', 'total_coins', 'activity_streak',
        'is_team_manager', 'is_active',
    )
    list_filter = ('is_team_manager', 'is_active')
    search_fields = ('username', 'first_name', 'last_name')
    ordering = ('-total_points',)

    def has_change_permission(self, request, obj=None):
        # The account form also edits credentials. Protect other privileged accounts.
        if obj is not None and obj.pk != request.user.pk and not request.user.is_superuser:
            if obj.is_staff or obj.is_superuser or obj.groups.exists() or obj.user_permissions.exists():
                return False
        return super().has_change_permission(request, obj)

    fieldsets = (
        ('اطلاعات حساب', {
            'fields': ('username', 'password', 'first_name', 'last_name', 'email')
        }),
        ('امتیازات و سکه‌ها', {
            'fields': ('total_points', 'total_coins', 'activity_streak', 'last_activity_date')
        }),
        ('نقش‌ها و دسترسی‌ها', {
            'fields': ('is_team_manager', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('زمان‌ها', {
            'fields': ('last_login', 'date_joined')
        }),
    )


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


@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'transaction_type', 'title',
        'points', 'coins', 'created_at',
    )
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('user__username', 'title')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)


# =====================================================================
# ماموریت‌ها
# =====================================================================

@admin.register(MissionCategory)
class MissionCategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'slug', 'icon_preview', 'order',
        'is_active', 'missions_count',
    )
    list_filter = ('is_active',)
    list_editable = ('order', 'is_active')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')

    fieldsets = (
        ('اطلاعات دسته‌بندی', {
            'fields': ('name', 'slug')
        }),
        ('ظاهر', {
            'fields': ('icon', 'color', 'order')
        }),
        ('وضعیت', {
            'fields': ('is_active',)
        }),
    )

    @admin.display(description="آیکون")
    def icon_preview(self, obj):
        return format_html(
            '<i class="fa-solid {}" style="color:{};font-size:1.3rem;"></i> '
            '<code style="font-size:0.8rem;">{}</code>',
            obj.icon, obj.color, obj.icon,
        )

    @admin.display(description="تعداد ماموریت")
    def missions_count(self, obj):
        return obj.missions.count()


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'category', 'points', 'coins',
        'is_global', 'show_on_home', 'home_order',
        'has_time_limit', 'is_active', 'created_at',
    )
    list_filter = (
        'is_active', 'is_global', 'show_on_home',
        'has_time_limit', 'category',
    )
    list_editable = (
        'points', 'coins', 'is_global',
        'show_on_home', 'home_order', 'is_active',
    )
    search_fields = ('title', 'description', 'created_by__username')
    ordering = ('home_order', '-created_at')
    readonly_fields = ('created_by', 'created_at')
    autocomplete_fields = ('category',)

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('title', 'description', 'category')
        }),
        ('پاداش‌ها', {
            'fields': ('points', 'coins')
        }),
        ('محدودیت زمانی', {
            'fields': ('has_time_limit', 'start_time', 'end_time')
        }),
        ('نمایش و دسترسی', {
            'fields': (
                'is_global', 'show_on_home', 'home_order', 'is_active',
            ),
            'description': (
                'اگر «ماموریت مشترک/ثابت» فعال باشد، این ماموریت '
                'در همه تیم‌ها به‌صورت خودکار فعال است.'
            )
        }),
        ('زمان ایجاد', {
            'fields': ('created_by', 'created_at')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TeamMission)
class TeamMissionAdmin(admin.ModelAdmin):
    list_display = (
        'team', 'mission', 'is_active',
        'effective_points', 'effective_coins', 'order', 'created_at',
    )
    list_filter = ('is_active', 'team', 'mission__category')
    search_fields = ('team__name', 'mission__title')
    autocomplete_fields = ('team', 'mission')
    list_editable = ('is_active', 'order')
    ordering = ('team', 'order')

    fieldsets = (
        ('اطلاعات اتصال', {
            'fields': ('team', 'mission', 'is_active', 'order')
        }),
        ('پاداش اختصاصی این تیم (اختیاری)', {
            'fields': ('points_override', 'coins_override'),
            'description': (
                'در صورت خالی بودن، از پاداش پیش‌فرض ماموریت استفاده می‌شود.'
            )
        }),
        ('زمان', {
            'fields': ('created_at',)
        }),
    )
    readonly_fields = ('created_at',)

    @admin.display(description="امتیاز مؤثر")
    def effective_points(self, obj):
        return obj.get_points()

    @admin.display(description="سکه مؤثر")
    def effective_coins(self, obj):
        return obj.get_coins()


@admin.register(MissionRequest)
class MissionRequestAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'mission', 'team', 'status_badge',
        'points_awarded', 'coins_awarded',
        'requested_at', 'reviewed_by',
    )
    list_filter = ('status', 'requested_at', 'team')
    search_fields = ('user__username', 'mission__title', 'note')
    readonly_fields = (
        'status', 'requested_at', 'reviewed_at', 'reviewed_by',
        'points_awarded', 'coins_awarded',
    )
    date_hierarchy = 'requested_at'
    autocomplete_fields = ('user', 'mission', 'team')

    fieldsets = (
        ('اطلاعات درخواست', {
            'fields': ('user', 'mission', 'team', 'note', 'status')
        }),
        ('بررسی', {
            'fields': (
                'admin_note', 'reviewed_by', 'reviewed_at',
                'points_awarded', 'coins_awarded',
            )
        }),
        ('زمان', {
            'fields': ('requested_at',)
        }),
    )

    actions = ['approve_requests', 'reject_requests']

    def save_model(self, request, obj, form, change):
        if change:
            obj.save(update_fields=form.changed_data)
        else:
            super().save_model(request, obj, form, change)

    @admin.display(description="وضعیت")
    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'approved': '#10b981',
            'rejected': '#ef4444',
        }
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            colors.get(obj.status, '#000'),
            obj.get_status_display(),
        )

    @admin.action(permissions=['change'], description="تأیید درخواست‌های انتخاب‌شده")
    def approve_requests(self, request, queryset):
        count = 0
        for mr in queryset.filter(status='pending'):
            if mr.approve(admin_user=request.user):
                count += 1
        self.message_user(request, f"{count} درخواست تأیید و امتیاز/سکه اهدا شد.")

    @admin.action(permissions=['change'], description="رد درخواست‌های انتخاب‌شده")
    def reject_requests(self, request, queryset):
        count = 0
        for mr in queryset.filter(status='pending'):
            if mr.reject(admin_user=request.user, admin_note="رد شده توسط مدیر"):
                count += 1
        self.message_user(request, f"{count} درخواست رد شد.")


@admin.register(MissionCompletion)
class MissionCompletionAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'mission', 'team',
        'points_awarded', 'coins_awarded', 'completed_at',
    )
    list_filter = ('completed_at', 'team', 'mission__category')
    search_fields = ('user__username', 'mission__title')
    date_hierarchy = 'completed_at'
    readonly_fields = ('completed_at', 'points_awarded', 'coins_awarded')
    autocomplete_fields = ('user', 'mission', 'team')


# =====================================================================
# بانک سوال
# =====================================================================

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text_preview', 'correct_option')
    list_filter = ('correct_option',)
    search_fields = ('text',)
    ordering = ('-id',)

    @admin.display(description="متن سوال")
    def text_preview(self, obj):
        return obj.text[:60]


# =====================================================================
# سوالات روزانه
# =====================================================================

@admin.register(DailyQuestion)
class DailyQuestionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'short_question', 'publish_date',
        'points', 'difficulty', 'is_active', 'answered_count',
    )
    list_filter = ('is_active', 'difficulty', 'publish_date')
    search_fields = ('question__text',)
    date_hierarchy = 'publish_date'
    list_editable = ('is_active',)
    autocomplete_fields = ('question',)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['add_question_url'] = reverse('admin:missions_question_add')
        return super().change_view(request, object_id, form_url, extra_context)

    @admin.display(description="سوال")
    def short_question(self, obj):
        return obj.question.text[:50]

    @admin.display(description="تعداد پاسخ‌ها")
    def answered_count(self, obj):
        return obj.answers.count()


@admin.register(DailyQuestionAnswer)
class DailyQuestionAnswerAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'daily_question', 'is_correct_badge',
        'selected_option', 'points_awarded', 'answered_at',
    )
    list_filter = ('is_correct', 'answered_at')
    search_fields = ('user__username', 'daily_question__question__text')
    date_hierarchy = 'answered_at'
    readonly_fields = ('answered_at',)

    @admin.display(description="وضعیت")
    def is_correct_badge(self, obj):
        if obj.is_correct:
            return format_html(
                '<span style="color:{};font-weight:bold;">{}</span>',
                'green', '✓ صحیح',
            )
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            'red', '✗ غلط',
        )


# =====================================================================
# مسابقات
# =====================================================================

class CompetitionQuestionInline(admin.TabularInline):
    model = CompetitionQuestion
    extra = 1
    autocomplete_fields = ('question',)
    ordering = ('order',)
    fields = ('question', 'order', 'points_override')


class CompetitionAdminForm(forms.ModelForm):
    def clean_status(self):
        status = self.cleaned_data['status']
        if status == 'finished':
            raise forms.ValidationError("برای پایان مسابقه از عملیات نهایی‌سازی استفاده کنید.")
        return status


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    form = CompetitionAdminForm
    list_display = (
        'title', 'status_badge', 'start_date', 'end_date',
        'is_featured', 'points_per_correct',
        'max_questions', 'registrations_count',
    )
    list_filter = ('status', 'is_featured', 'start_date')
    search_fields = ('title', 'description')
    date_hierarchy = 'start_date'
    inlines = [CompetitionQuestionInline]

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('title', 'description', 'is_featured', 'status')
        }),
        ('دوره زمانی', {
            'fields': ('start_date', 'end_date')
        }),
        ('امتیازدهی و محدودیت‌ها', {
            'fields': ('points_per_correct', 'max_questions', 'time_limit_minutes')
        }),
        ('جوایز', {
            'fields': (
                'first_prize_points', 'second_prize_points',
                'third_prize_points', 'participation_bonus',
            )
        }),
    )

    actions = ['finalize_competition', 'activate_competitions']

    def get_readonly_fields(self, request, obj=None):
        if obj is not None and obj.status == 'finished':
            return (*super().get_readonly_fields(request, obj), 'status')
        return super().get_readonly_fields(request, obj)

    def save_model(self, request, obj, form, change):
        if not change:
            return super().save_model(request, obj, form, change)
        fields = set(form.changed_data)
        if 'status' in fields:
            Competition.objects.filter(pk=obj.pk).exclude(status='finished').update(status=obj.status)
            fields.remove('status')
        obj.save(update_fields=fields)
        obj.refresh_from_db(fields=['status'])

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['add_question_url'] = reverse('admin:missions_question_add')
        return super().change_view(request, object_id, form_url, extra_context)

    @admin.display(description="وضعیت")
    def status_badge(self, obj):
        colors = {
            'draft': 'gray', 'upcoming': 'orange', 'active': 'green',
            'finished': 'blue', 'cancelled': 'red',
        }
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display(),
        )

    @admin.display(description="شرکت‌کنندگان")
    def registrations_count(self, obj):
        return obj.registrations.count()

    @admin.action(description="پایان مسابقه و اهدای جوایز")
    def finalize_competition(self, request, queryset):
        count = 0
        for comp in queryset:
            if comp.finalize():
                count += 1
        self.message_user(request, f"{count} مسابقه پایان یافت و جوایز اهدا شد.")

    @admin.action(description="فعال‌سازی مسابقات انتخاب‌شده")
    def activate_competitions(self, request, queryset):
        count = queryset.exclude(status='finished').update(status='active')
        self.message_user(request, f"{count} مسابقه فعال شد.")


@admin.register(CompetitionQuestion)
class CompetitionQuestionAdmin(admin.ModelAdmin):
    list_display = (
        'competition', 'question_short', 'order',
        'points_override', 'effective_points',
    )
    list_filter = ('competition',)
    search_fields = ('competition__title', 'question__text')
    autocomplete_fields = ('question',)
    ordering = ('competition', 'order')

    @admin.display(description="سوال")
    def question_short(self, obj):
        return obj.question.text[:50]

    @admin.display(description="امتیاز مؤثر")
    def effective_points(self, obj):
        return obj.get_points()


@admin.register(CompetitionRegistration)
class CompetitionRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'competition', 'total_correct', 'total_wrong',
        'total_answered', 'score', 'rank', 'is_completed',
    )
    list_filter = ('is_completed', 'competition')
    search_fields = ('user__username', 'competition__title')
    readonly_fields = ('registered_at', 'started_at', 'finished_at', 'is_completed')
    date_hierarchy = 'registered_at'
    autocomplete_fields = ('user', 'competition')

    def save_model(self, request, obj, form, change):
        if change:
            obj.save(update_fields=form.changed_data)
        else:
            super().save_model(request, obj, form, change)


@admin.register(CompetitionAnswer)
class CompetitionAnswerAdmin(admin.ModelAdmin):
    list_display = (
        'registration', 'question_short', 'selected_option',
        'is_correct_badge', 'points_awarded', 'answered_at',
    )
    list_filter = ('is_correct', 'answered_at', 'registration__competition')
    search_fields = ('registration__user__username', 'question__text')
    readonly_fields = ('answered_at',)
    date_hierarchy = 'answered_at'
    autocomplete_fields = ('question',)

    @admin.display(description="سوال")
    def question_short(self, obj):
        return obj.question.text[:50]

    @admin.display(description="وضعیت")
    def is_correct_badge(self, obj):
        if obj.is_correct:
            return format_html(
                '<span style="color:{};font-weight:bold;">{}</span>',
                'green', '✓ صحیح',
            )
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            'red', '✗ غلط',
        )


# =====================================================================
# صندوق گنج
# =====================================================================

@admin.register(TreasureCategory)
class TreasureCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon_preview', 'order', 'is_active', 'items_count')
    list_filter = ('is_active',)
    list_editable = ('order', 'is_active')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')

    fieldsets = (
        ('اطلاعات دسته‌بندی', {
            'fields': ('name', 'slug')
        }),
        ('ظاهر', {
            'fields': ('icon', 'color', 'order')
        }),
        ('وضعیت', {
            'fields': ('is_active',)
        }),
    )

    @admin.display(description="آیکون")
    def icon_preview(self, obj):
        return format_html(
            '<i class="fa-solid {}" style="color:{};font-size:1.3rem;"></i> '
            '<code style="font-size:0.8rem;">{}</code>',
            obj.icon, obj.color, obj.icon,
        )

    @admin.display(description="تعداد آیتم")
    def items_count(self, obj):
        return obj.items.count()


@admin.register(TreasureItem)
class TreasureItemAdmin(admin.ModelAdmin):
    list_display = (
        'image_preview', 'name', 'category', 'price',
        'stock_display', 'is_featured', 'is_active', 'created_at',
    )
    list_filter = ('category', 'is_featured', 'is_active')
    list_editable = ('is_featured', 'is_active', 'price')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'image_preview_large')
    autocomplete_fields = ('category',)

    fieldsets = (
        ('اطلاعات آیتم', {
            'fields': ('name', 'description', 'category')
        }),
        ('تصویر', {
            'fields': ('image', 'image_preview_large')
        }),
        ('قیمت و موجودی', {
            'fields': ('price', 'stock', 'is_featured', 'is_active')
        }),
        ('زمان', {
            'fields': ('created_at',)
        }),
    )

    @admin.display(description="تصویر")
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:50px;height:50px;'
                'object-fit:cover;border-radius:8px;" />',
                obj.image.url
            )
        return "—"

    @admin.display(description="پیش‌نمایش تصویر")
    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:300px;border-radius:12px;" />',
                obj.image.url
            )
        return "—"

    @admin.display(description="موجودی")
    def stock_display(self, obj):
        if obj.stock is None:
            return format_html('<span style="color:green;">نامحدود</span>')
        if obj.stock == 0:
            return format_html('<span style="color:red;font-weight:bold;">ناموجود</span>')
        if obj.stock <= 3:
            return format_html(
                '<span style="color:orange;font-weight:bold;">{} (کم)</span>',
                obj.stock
            )
        return obj.stock


@admin.register(TreasurePurchase)
class TreasurePurchaseAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'item_name', 'item_price',
        'status_badge', 'purchased_at', 'delivered_at',
    )
    list_filter = ('status', 'purchased_at')
    search_fields = ('user__username', 'item_name')
    readonly_fields = ('user', 'item', 'item_name', 'item_price', 'purchased_at', 'delivered_at')
    date_hierarchy = 'purchased_at'

    fieldsets = (
        ('اطلاعات خرید', {
            'fields': ('user', 'item', 'item_name', 'item_price', 'purchased_at')
        }),
        ('وضعیت', {
            'fields': ('status', 'admin_note', 'delivered_at')
        }),
    )

    actions = ['mark_delivered']

    @admin.display(description="وضعیت")
    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'delivered': '#10b981',
            'cancelled': '#ef4444',
        }
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            colors.get(obj.status, '#000'),
            obj.get_status_display(),
        )

    @admin.action(description="علامت‌گذاری به‌عنوان تحویل شده")
    def mark_delivered(self, request, queryset):
        count = 0
        for p in queryset.filter(status='pending'):
            if p.deliver():
                count += 1
        self.message_user(request, f"{count} خرید به‌عنوان تحویل شده علامت‌گذاری شد.")
