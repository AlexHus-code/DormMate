from django.contrib.auth.models import AbstractUser
from django.db import models
# registration/models.py

from django.contrib.auth import get_user_model
from django.conf import settings
from rooms.models import Room  # Импорт модели Room


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Студент'),
        ('admin', 'Адміністратор'),
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


User = get_user_model()

class Petition(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    description = models.TextField(verbose_name="Опис")
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='petitions')
    votes = models.ManyToManyField(User, related_name='voted_petitions', blank=True)

    def total_votes(self):
        return self.votes.count()

    def __str__(self):
        return self.title

class PetitionResponse(models.Model):
    petition = models.ForeignKey(Petition, on_delete=models.CASCADE, related_name='responses')
    responder = models.ForeignKey(User, on_delete=models.CASCADE)
    response_text = models.TextField(verbose_name="Відповідь")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response by {self.responder.username} on {self.petition.title}"
    

class News(models.Model):
    title = models.CharField("Заголовок", max_length=255)
    content = models.TextField("Текст")
    image = models.ImageField("Зображення", upload_to="news_images/", default="news_images/default.png", blank=True)
    created_at = models.DateTimeField("Дата створення", auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")

    class Meta:
        verbose_name = "Новина"
        verbose_name_plural = "Новини"
        ordering = ['-created_at']

    def __str__(self):
        return self.title