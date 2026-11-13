from apps.accounts.services.roles import toggle_active, toggle_staff, toggle_team_manager
from apps.accounts.selectors.staff import get_staff_user_detail_context, get_staff_user_list_context
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from apps.accounts.models import User
from apps.accounts.models import User
from apps.backoffice.decorators import staff_required


@staff_required
def users_list(request):
    """لیست کاربران با جستجو و فیلتر"""
    q = request.GET.get('q', '').strip()
    role = request.GET.get('role', '')
    team_id = request.GET.get('team', '')

    context = get_staff_user_list_context(q, role, team_id)
    return render(request, 'dashboard/users.html', context)


@staff_required
def user_detail(request, user_id):
    """پروفایل کاربر از دید مدیر"""
    user = get_object_or_404(User, id=user_id)

    context = get_staff_user_detail_context(user)
    return render(request, 'dashboard/user_detail.html', context)


@staff_required
@require_POST
def user_toggle_staff(request, user_id):
    if not request.user.is_superuser:
        raise PermissionDenied
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        messages.error(request, 'نمی‌توانید وضعیت خودتان را تغییر دهید.')
        return redirect('dashboard:user_detail', user_id=user.id)
    toggle_staff(user)
    messages.success(
        request,
        f'دسترسی کارمندی «{user.username}» {"فعال" if user.is_staff else "غیرفعال"} شد.'
    )
    return redirect('dashboard:user_detail', user_id=user.id)


@staff_required
@require_POST
def user_toggle_manager(request, user_id):
    user = get_object_or_404(User, id=user_id)
    toggle_team_manager(user)
    messages.success(
        request,
        f'وضعیت مدیریت تیم «{user.username}» {"فعال" if user.is_team_manager else "غیرفعال"} شد.'
    )
    return redirect('dashboard:user_detail', user_id=user.id)


@staff_required
@require_POST
def user_toggle_active(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        messages.error(request, 'نمی‌توانید حساب خودتان را غیرفعال کنید.')
        return redirect('dashboard:user_detail', user_id=user.id)
    toggle_active(user)
    messages.success(
        request,
        f'حساب «{user.username}» {"فعال" if user.is_active else "غیرفعال"} شد.'
    )
    return redirect('dashboard:user_detail', user_id=user.id)
