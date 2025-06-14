from django.db import models
from django.conf import settings  
from django.contrib.auth.models import User
# Create your models here.

# models.py


class Room(models.Model):
    number = models.CharField(max_length=10)
    floor = models.IntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    capacity = models.IntegerField()
    about = models.TextField(default="Звичайна кімната")
    image = models.ImageField(upload_to='room_images/', default='room_images/default.jpg')

    residents = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='shared_rooms'
    )

    def occupancy_status(self):
        count = self.residents.count()
        if count >= self.capacity:
            return "full"
        elif count == 0:
            return "empty"
        else:
            return "partial"

    def occupied_slots(self):
        return self.residents.count()

    def free_slots(self):
        return self.capacity - self.residents.count()

    def __str__(self):
        return f"Комната {self.number} (этаж {self.floor})"


class Application(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    room_number = models.IntegerField()
    medical_doc = models.FileField(upload_to='applications/')
    bank_receipt = models.FileField(upload_to='applications/')
    application = models.FileField(upload_to='applications/')
    student_card = models.FileField(upload_to='applications/')
    application_partion_pay = models.FileField(upload_to='applications/', blank=True)
    aplication_parent_pay = models.FileField(upload_to='applications/', blank=True )
    contract = models.FileField(upload_to='applications/')
    personal_account = models.FileField(upload_to='applications/')
    comment = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Очікує розгляду'),
        ('approved', 'Прийнята'),
        ('rejected', 'Відхилена'),
    ])
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    def __str__(self):
        return f"Заявка от {self.user.username} на кімнату {self.room_number}"