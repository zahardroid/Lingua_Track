from django.db import models
from django.utils import timezone
from cards.models import Card


class Schedule(models.Model):
    """
    Модель для хранения расписания повторений по алгоритму SM-2.
    """
    card = models.OneToOneField(
        Card,
        on_delete=models.CASCADE,
        related_name='schedule',
        verbose_name='Карточка'
    )
    next_review_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Следующее повторение'
    )
    interval = models.IntegerField(
        default=1,
        verbose_name='Интервал (дни)'
    )
    repetitions = models.IntegerField(
        default=0,
        verbose_name='Количество повторений'
    )
    easiness_factor = models.FloatField(
        default=2.5,
        verbose_name='Фактор легкости'
    )
    last_reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Последнее повторение'
    )

    class Meta:
        verbose_name = 'Расписание'
        verbose_name_plural = 'Расписания'
        ordering = ['next_review_at']
        indexes = [
            models.Index(fields=['next_review_at']),
            models.Index(fields=['card']),
        ]

    def __str__(self):
        return f"Schedule for {self.card.word} - Next: {self.next_review_at}"

