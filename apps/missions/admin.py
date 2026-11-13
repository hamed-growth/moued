from django.contrib import admin
from django.utils.html import format_html
from apps.missions.models import (
    Mission,
    MissionCategory,
    MissionCompletion,
    MissionRequest,
    TeamMission,
)


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
