# forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Room, Petition,PetitionResponse,News,User
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import PasswordChangeForm

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']
        labels = {
            'username': 'Ім’я користувача',
            'email': 'Електронна пошта',
            'password1': 'Пароль',
            'password2': 'Підтвердження паролю',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Ім’я користувача'
        self.fields['email'].label = 'Електронна пошта'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Підтвердження паролю'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Користувач з такою електронною поштою вже існує.")
        return email
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.help_text = ''


class AdminCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Користувач з такою електронною поштою вже існує.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'admin'  # Присвоюємо роль адміністратора
        if commit:
            user.save()
        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Убираем стандартные help_text
        for field in self.fields.values():
            field.help_text = ''

        # Устанавливаем кастомные метки (украинские)
        self.fields['username'].label = 'Імʼя користувача'
        self.fields['email'].label = 'Електронна пошта'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Підтвердження пароля'

    

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['number', 'floor', 'price', 'capacity', 'about', 'image']
        widgets = {
            'about': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['about'].initial = 'Звичайна кімната'

class RoomGroupForm(forms.Form):
    count = forms.IntegerField(min_value=1, label="Кількість кімнат на кожному поверсі")
    floors = forms.CharField(label="Поверхи (через кому, наприклад: 1,2,3)")
    price = forms.DecimalField(max_digits=8, decimal_places=2)
    capacity = forms.IntegerField(min_value=1)
    about = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    image = forms.ImageField(label="Зображення кімнати", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['about'].initial = 'Звичайна кімната'




class PetitionForm(forms.ModelForm):
    class Meta:
        model = Petition
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Назва петиції'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Опишіть свою петицію'}),
        }
        labels = {
            'title': 'Назва',
            'description': 'Опис',
        }


class PetitionResponseForm(forms.ModelForm):
    class Meta:
        model = PetitionResponse
        fields = ['response_text']
        widgets = {
            'response_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Ваша відповідь...'}),
        }


class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ['title', 'content', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control'}),
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email']
        labels = {
            'username': 'Ім’я користувача',
            'email': 'Електронна пошта',
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.help_text = ''

class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(label="Старий пароль", widget=forms.PasswordInput)
    new_password1 = forms.CharField(label="Новий пароль", widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="Підтвердження пароля", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.help_text = ''