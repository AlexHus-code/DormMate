from django import forms
from .models import Application

class ApplicationModelForm(forms.ModelForm):
    class Meta:
        model = Application
        exclude = ['user', 'status']
        labels = {
            'room_number': 'Номер кімнати',
            'medical_doc': 'Медична довідка',
            'bank_receipt': 'Квитанція про оплату',
            'application': 'Заява',
            'student_card': 'Студентський квиток',
            'application_partion_pay': 'Заява на часткову оплату',
            'aplication_parent_pay': 'Заява від батьків на оплату',
            'contract': 'Контракт',
            'personal_account': 'Особовий рахунок',
            'comment': 'Коментар',
        }