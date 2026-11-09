from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


class UserRegisterForm(UserCreationForm):
    """فرم ثبت‌نام کاربر"""
    email = forms.EmailField(required=True, label="ایمیل")
    first_name = forms.CharField(required=False, label="نام")
    last_name = forms.CharField(required=False, label="نام خانوادگی")

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label


class UserLoginForm(AuthenticationForm):
    """فرم ورود کاربر"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label