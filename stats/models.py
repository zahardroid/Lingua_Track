from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    """
    Расширенный профиль пользователя с Telegram ID.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь'
    )
    telegram_id = models.BigIntegerField(
        null=True,
        blank=True,
        unique=True,
        verbose_name='Telegram ID'
    )
    telegram_username = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Telegram Username'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'
        indexes = [
            models.Index(fields=['telegram_id']),
        ]

    def __str__(self):
        return f"Profile for {self.user.username}"


class Stats(models.Model):
    """
    Модель для хранения статистики пользователя.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='stats',
        verbose_name='Пользователь'
    )
    total_words = models.IntegerField(default=0, verbose_name='Всего слов')
    learned_words = models.IntegerField(default=0, verbose_name='Изучено слов')
    total_reviews = models.IntegerField(default=0, verbose_name='Всего повторений')
    wrong_answers = models.IntegerField(default=0, verbose_name='Неправильных ответов')
    last_review_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Последнее повторение'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        verbose_name = 'Статистика'
        verbose_name_plural = 'Статистика'
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"Stats for {self.user.username}"

    @property
    def success_rate(self):
        """Процент правильных ответов."""
        if self.total_reviews == 0:
            return 0
        correct = self.total_reviews - self.wrong_answers
        return round((correct / self.total_reviews) * 100, 2)
