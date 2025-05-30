# forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Room
from django.core.exceptions import ValidationError


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким адресом электронной почты уже существует.")
        return email


class AdminCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким адресом электронной почты уже существует.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'admin'  # Присваиваем роль администратора
        if commit:
            user.save()
        return user
    

    

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['number', 'floor', 'price', 'capacity', 'about', 'image']
        widgets = {
            'about': forms.Textarea(attrs={'rows': 4}),
        }