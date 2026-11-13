from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password

from .models import User


class UserRegisterForm(forms.ModelForm):
    email = forms.EmailField(label='ایمیل', required=True)
    password = forms.CharField(label='گذرواژه', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if len(username) < 3:
            raise forms.ValidationError('نام کاربری حداقل ۳ حرف باشد.')
        return username

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()

    def clean_password(self):
        password = self.cleaned_data['password']
        candidate = User(username=self.data.get('username', '').strip(), email=self.data.get('email', '').strip())
        validate_password(password, candidate)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='نام کاربری یا ایمیل')
    remember_me = forms.BooleanField(label='مرا به خاطر بسپار', required=False, initial=True)

    def clean_username(self):
        identifier = self.cleaned_data['username'].strip()
        if '@' not in identifier:
            return identifier
        usernames = list(User.objects.filter(email__iexact=identifier).values_list('username', flat=True)[:2])
        return usernames[0] if len(usernames) == 1 else identifier
