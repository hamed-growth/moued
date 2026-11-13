from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def staff_required(view_func):
    """
    فقط کارمندها (is_staff=True) یا سوپریوزرها اجازه دسترسی دارند.
    """
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        user = request.user
        if not (user.is_staff or user.is_superuser):
            messages.error(request, 'شما دسترسی به داشبورد مدیریت را ندارید.')
            return redirect('missions:home')
        return view_func(request, *args, **kwargs)
    return _wrapped