from django.contrib.auth.models import AbstractUser
from django.db import models
# registration/models.py

from django.conf import settings
from rooms.models import Room  # Импорт модели Room


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Студент'),
        ('admin', 'Администратор'),
    )

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')

    # Связь с основной комнатой проживания — related_name НЕ должен конфликтовать
    room = models.ForeignKey(
        'rooms.Room',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='primary_users'  # ← обязательно уникальное имя
    )

    def __str__(self):
        return self.username

