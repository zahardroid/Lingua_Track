"""
Сигналы Django для автоматического создания расписания при создании карточки.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Card
from schedules.services import SM2Service


@receiver(post_save, sender=Card)
def create_schedule_for_card(sender, instance, created, **kwargs):
    """
    Автоматически создает расписание для новой карточки.
    """
    if created:
        SM2Service.initialize_schedule(instance)

