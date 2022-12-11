from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.hashers import make_password
from django.utils.translation import ugettext, ugettext_lazy as _
from django.urls import reverse_lazy
from django.template.loader import render_to_string
from django.template import loader
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import (
    AuthenticationForm,PasswordResetForm,UsernameField
)

class UserCreateForm(UserCreationForm):
    email = forms.EmailField(label="メールアドレス", required=True)
    last_name = forms.CharField(label='姓', required=True)
    first_name = forms.CharField(label='名', required=True)
    password1 = forms.CharField(label='パスワード', required=True, strip=False, widget=forms.PasswordInput())
    password2 = forms.CharField(label='パスワード確認', required=True, strip=False, widget=forms.PasswordInput())
    class Meta:
        model = User
        fields = ("email", "last_name", "first_name", "password1", "password2")

    def clean(self):
        super(UserCreateForm, self).clean()
        try:
            user = User.objects.get(email=self.cleaned_data['email'])
            raise forms.ValidationError("同じメールを持つユーザーが既に存在します。")
        except User.DoesNotExist:
            pass

    def save(self, commit=True):
        user = super(UserCreateForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        user.username = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.is_active = True
        user.save()
        return user

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(label="メールアドレス", required=True)
    last_name = forms.CharField(label='姓', required=True)
    first_name = forms.CharField(label='名', required=True)
    is_superuser = forms.IntegerField(label='ロール', required=True)
    
    class Meta:
        model = User
        fields = ("email", "last_name", "first_name", "is_superuser")

    def save(self, commit=True):
        user = super(UserUpdateForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        user.username = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.is_superuser = self.cleaned_data["is_superuser"]
        if commit:
            user.save()
        return user

class ProfiledAuthenticationForm(AuthenticationForm):
    username = UsernameField(
        label=_("メールアドレス"),
        max_length=254,
        widget=forms.TextInput(attrs={'autofocus': True,'placeholder': 'メールアドレス'}),
    )
    password = forms.CharField(
        label=_("パスワード"),
        strip=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'パスワード'}),
    )
    #remember_me = forms.BooleanField(required=False,widget=forms.CheckboxInput(attrs={'class':'scalero-checkbox','id':'remember-me'}))
    profile_error_messages = {
        "invalid_profile": _("メールアドレスまたはパスワードが正しくありません。"
        )
    }
    error_messages = {
        'invalid_login': _(
            "ログインできません。パスワードが分からない場合、管理者に連絡してください。"            
        ),
        
    }
    def clean(self):
        super(ProfiledAuthenticationForm, self).clean()
        # if self.user_cache:
        #     if not self.user_cache.twitteruser.can_login:
        #         raise forms.ValidationError(
        #             self.profile_error_messages['invalid_profile'],
        #             code='invalid_profile',
        #             params={'username': self.username_field.verbose_name},
        #         )