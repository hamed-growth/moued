"""Same-origin session auth for an API frontend; CSRF remains mandatory."""

import json

from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.utils.cache import add_never_cache_headers
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from apps.accounts.forms import UserLoginForm, UserRegisterForm
from .serializers import MeSerializer


def _response(payload, status=200):
    response = JsonResponse(payload, status=status)
    add_never_cache_headers(response)
    return response


def _json_payload(request):
    if request.content_type != "application/json":
        return None, _response({"code": "unsupported_media_type", "message": "JSON body required"}, 415)
    try:
        data = json.loads(request.body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, _response({"code": "invalid_json", "message": "Invalid JSON body"}, 400)
    if not isinstance(data, dict):
        return None, _response({"code": "invalid_json", "message": "Expected a JSON object"}, 400)
    return data, None


@require_GET
@ensure_csrf_cookie
def csrf_cookie(request):
    return _response({"ok": True})


@require_POST
@csrf_protect
def session_login(request):
    data, error = _json_payload(request)
    if error is not None:
        return error
    if not isinstance(data.get("username"), str) or not isinstance(data.get("password"), str):
        return _response({"code": "invalid_input", "message": "username and password are required"}, 400)
    if len(data["username"]) > 254 or len(data["password"]) > 4096:
        return _response({"code": "invalid_input", "message": "Invalid credentials"}, 400)
    if "remember_me" in data and not isinstance(data["remember_me"], bool):
        return _response({"code": "invalid_input", "message": "remember_me must be boolean"}, 400)
    form = UserLoginForm(request, data={
        "username": data["username"], "password": data["password"],
        "remember_me": data.get("remember_me", False),
    })
    if not form.is_valid():
        return _response({"code": "invalid_credentials", "message": "Invalid credentials"}, 401)
    login(request, form.get_user())
    request.session.set_expiry(90 * 24 * 60 * 60 if form.cleaned_data["remember_me"] else 0)
    return _response({"user": MeSerializer(request.user).data})


@require_POST
@csrf_protect
def session_register(request):
    data, error = _json_payload(request)
    if error is not None:
        return error
    # Never accept privilege, balance, or ownership fields from the client.
    form = UserRegisterForm(data={key: data.get(key) for key in ("username", "email", "password")})
    if not form.is_valid():
        return _response({
            "code": "validation_error", "message": "Invalid registration data",
            "field_errors": {key: list(values) for key, values in form.errors.items()},
        }, 400)
    user = form.save()
    login(request, user)
    return _response({"user": MeSerializer(user).data}, 201)


@require_POST
@csrf_protect
def session_logout(request):
    if not request.user.is_authenticated:
        return _response({"code": "not_authenticated", "message": "Login required"}, 401)
    logout(request)
    return _response({"ok": True})
