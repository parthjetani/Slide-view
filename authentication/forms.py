from django import forms
from django.contrib.auth.models import User
from .models import CustomUser


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')


class CustomForm(forms.ModelForm):
    avatar = forms.ImageField(widget=forms.widgets.FileInput)
    class Meta:
        model = CustomUser
        fields = ("organization_name", 'organization_role', 'phone_number', 'avatar')
