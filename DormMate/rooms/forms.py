from django import forms
from .models import Application

class ApplicationModelForm(forms.ModelForm):
    class Meta:
        model = Application
        exclude = ['user', 'status']