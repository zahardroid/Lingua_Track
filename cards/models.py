from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Card(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Начальный'),
        ('intermediate', 'Средний'),
        ('advanced', 'Продвинутый'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cards')
    word = models.CharField(max_length=200, verbose_name='Слово')
    translation = models.CharField(max_length=200, verbose_name='Перевод')
    example = models.TextField(blank=True, null=True, verbose_name='Пример использования')
    note = models.TextField(blank=True, null=True, verbose_name='Заметка')
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default='beginner',
        verbose_name='Уровень'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        verbose_name = 'Карточка'
        verbose_name_plural = 'Карточки'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'level']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.word} - {self.translation}"

