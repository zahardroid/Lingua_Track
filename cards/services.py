"""
Сервисы для работы с карточками.
"""
from django.db import transaction
from django.contrib.auth.models import User
from .models import Card
from schedules.services import SM2Service
from stats.models import Stats


class CardService:
    """Сервис для работы с карточками."""
    
    @staticmethod
    @transaction.atomic
    def create_card(user: User, word: str, translation: str, example: str = None,
                   note: str = None, level: str = 'beginner') -> Card:
        """
        Создает новую карточку и инициализирует для неё расписание.
        
        Args:
            user: Пользователь Django
            word: Слово
            translation: Перевод
            example: Пример использования
            note: Заметка
            level: Уровень сложности
        
        Returns:
            Card: Созданная карточка
        """
        card = Card.objects.create(
            user=user,
            word=word,
            translation=translation,
            example=example or '',
            note=note or '',
            level=level
        )
        
        # Расписание создается автоматически через сигнал post_save
        # SM2Service.initialize_schedule(card)  # Убрано, т.к. есть сигнал
        
        # Обновляем статистику
        stats, _ = Stats.objects.get_or_create(user=user)
        stats.total_words += 1
        stats.save()
        
        return card
    
    @staticmethod
    def get_user_cards(user: User, level: str = None):
        """
        Получает карточки пользователя с опциональной фильтрацией по уровню.
        
        Args:
            user: Пользователь Django
            level: Уровень для фильтрации (опционально)
        
        Returns:
            QuerySet: Карточки пользователя
        """
        queryset = Card.objects.filter(user=user)
        if level:
            queryset = queryset.filter(level=level)
        return queryset.select_related('schedule')
    
    @staticmethod
    @transaction.atomic
    def delete_card(card: Card):
        """
        Удаляет карточку и обновляет статистику.
        
        Args:
            card: Объект Card для удаления
        """
        user = card.user
        card.delete()
        
        # Обновляем статистику
        stats, _ = Stats.objects.get_or_create(user=user)
        stats.total_words = max(0, stats.total_words - 1)
        stats.save()

