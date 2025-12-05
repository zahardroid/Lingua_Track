"""
Сервис для работы с интервальным повторением по алгоритму SM-2.
"""
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from .models import Schedule
from cards.models import Card


class SM2Service:
    """
    Реализация алгоритма SuperMemo 2 для интервального повторения.
    """
    
    @staticmethod
    def calculate_next_review(quality: int, schedule: Schedule) -> tuple:
        """
        Вычисляет следующее повторение на основе качества ответа.
        
        Args:
            quality: Качество ответа (0-5)
                    0 - полное незнание
                    1 - неправильный ответ, но вспомнил
                    2 - неправильный ответ, но легко вспомнил
                    3 - правильный ответ с трудом
                    4 - правильный ответ после размышления
                    5 - правильный ответ легко
            schedule: Объект Schedule
        
        Returns:
            tuple: (новый интервал, новый easiness_factor, новые repetitions)
        """
        if quality < 3:
            # Неправильный ответ - начинаем заново
            new_interval = 1
            new_repetitions = 0
            new_easiness_factor = max(1.3, schedule.easiness_factor - 0.2)
        else:
            # Правильный ответ
            if schedule.repetitions == 0:
                new_interval = 1
            elif schedule.repetitions == 1:
                new_interval = 6
            else:
                new_interval = int(schedule.interval * schedule.easiness_factor)
            
            new_repetitions = schedule.repetitions + 1
            
            # Обновляем easiness_factor
            new_easiness_factor = schedule.easiness_factor + (
                0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
            )
            new_easiness_factor = max(1.3, new_easiness_factor)
        
        return new_interval, new_easiness_factor, new_repetitions
    
    @staticmethod
    @transaction.atomic
    def update_schedule(card: Card, quality: int) -> Schedule:
        """
        Обновляет расписание карточки после повторения.
        
        Args:
            card: Объект Card
            quality: Качество ответа (0-5)
        
        Returns:
            Schedule: Обновленный объект Schedule
        """
        schedule, created = Schedule.objects.get_or_create(
            card=card,
            defaults={
                'next_review_at': timezone.now(),
                'interval': 1,
                'repetitions': 0,
                'easiness_factor': 2.5,
            }
        )
        
        new_interval, new_easiness_factor, new_repetitions = SM2Service.calculate_next_review(
            quality, schedule
        )
        
        schedule.interval = new_interval
        schedule.easiness_factor = new_easiness_factor
        schedule.repetitions = new_repetitions
        schedule.next_review_at = timezone.now() + timedelta(days=new_interval)
        schedule.last_reviewed_at = timezone.now()
        schedule.save()
        
        return schedule
    
    @staticmethod
    def get_cards_for_today(user) -> list:
        """
        Получает список карточек для повторения сегодня.
        
        Args:
            user: Пользователь Django
        
        Returns:
            list: Список карточек Card
        """
        now = timezone.now()
        cards = Card.objects.filter(
            user=user,
            schedule__next_review_at__lte=now
        ).select_related('schedule').order_by('schedule__next_review_at')
        
        return list(cards)
    
    @staticmethod
    def initialize_schedule(card: Card) -> Schedule:
        """
        Инициализирует расписание для новой карточки.
        
        Args:
            card: Объект Card
        
        Returns:
            Schedule: Созданный объект Schedule
        """
        schedule, created = Schedule.objects.get_or_create(
            card=card,
            defaults={
                'next_review_at': timezone.now(),
                'interval': 1,
                'repetitions': 0,
                'easiness_factor': 2.5,
            }
        )
        return schedule

