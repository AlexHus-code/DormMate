# Generated by Django 5.2.1 on 2025-06-02 21:05

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Petition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Заголовок')),
                ('description', models.TextField(verbose_name='Опис')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='petitions', to=settings.AUTH_USER_MODEL)),
                ('votes', models.ManyToManyField(blank=True, related_name='voted_petitions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
