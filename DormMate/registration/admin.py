
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('role',)}),
    )
    list_display = ['username', 'email', 'role', 'is_staff']

admin.site.register(CustomUser, CustomUserAdmin)
