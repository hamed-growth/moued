from django.contrib.auth import login, logout
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.cache import add_never_cache_headers
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST

from .forms import UserLoginForm, UserRegisterForm


def _no_store(response):
    add_never_cache_headers(response)
    return response


def _safe_next(request):
    candidate = request.POST.get('next') or request.GET.get('next') or ''
    if url_has_allowed_host_and_scheme(candidate, {request.get_host()}, require_https=request.is_secure()):
        return candidate
    return reverse('missions:dashboard')


@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.user.is_authenticated:
        return _no_store(redirect('missions:dashboard'))
    form = UserLoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        request.session.set_expiry(90 * 24 * 60 * 60 if form.cleaned_data['remember_me'] else 0)
        return _no_store(redirect(_safe_next(request)))
    return _no_store(render(request, 'missions/login.html', {'form': form, 'next': _safe_next(request)}))


@require_http_methods(['GET', 'POST'])
def register_view(request):
    if request.user.is_authenticated:
        return _no_store(redirect('missions:dashboard'))
    form = UserRegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return _no_store(redirect('missions:mission_list'))
    return _no_store(render(request, 'missions/register.html', {'form': form}))


@require_POST
def logout_view(request):
    logout(request)
    return _no_store(redirect('missions:home'))
