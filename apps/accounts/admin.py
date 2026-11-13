from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from apps.accounts.models import User


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
