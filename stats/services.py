"""
Сервисы для работы со статистикой.
"""
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from cards.models import Card
from schedules.models import Schedule
from .models import Stats


class StatsService:
    """Сервис для работы со статистикой."""
    
    @staticmethod
    def get_user_stats(user: User) -> dict:
        """
        Получает полную статистику пользователя.
        
        Args:
            user: Пользователь Django
        
        Returns:
            dict: Словарь со статистикой
        """
        stats, _ = Stats.objects.get_or_create(user=user)
        
        # Подсчитываем изученные слова (с повторениями > 3)
        learned_count = Schedule.objects.filter(
            card__user=user,
            repetitions__gte=3
        ).count()
        
        stats.learned_words = learned_count
        stats.save()
        
        # Статистика по уровням
        level_stats = Card.objects.filter(user=user).values('level').annotate(
            count=Count('id')
        )
        
        # Карточки для повторения сегодня
        today_cards = Schedule.objects.filter(
            card__user=user,
            next_review_at__lte=timezone.now()
        ).count()
        
        # Статистика за последние 7 дней
        week_ago = timezone.now() - timedelta(days=7)
        recent_reviews = Schedule.objects.filter(
            card__user=user,
            last_reviewed_at__gte=week_ago
        ).count()
        
        return {
            'stats': stats,
            'level_stats': {item['level']: item['count'] for item in level_stats},
            'today_cards': today_cards,
            'recent_reviews': recent_reviews,
            'success_rate': stats.success_rate,
        }
    
    @staticmethod
    def get_recommendations(user: User) -> list:
        """
        Получает рекомендации для пользователя.
        
        Args:
            user: Пользователь Django
        
        Returns:
            list: Список рекомендаций
        """
        recommendations = []
        stats = StatsService.get_user_stats(user)
        
        # Рекомендация по начальным словам
        beginner_cards = Card.objects.filter(user=user, level='beginner')
        beginner_without_schedule = beginner_cards.exclude(schedule__repetitions__gte=3)
        if beginner_without_schedule.exists():
            recommendations.append({
                'type': 'beginner',
                'message': f'Повтори {beginner_without_schedule.count()} начальных слов',
                'count': beginner_without_schedule.count()
            })
        
        # Рекомендация по среднему уровню
        intermediate_cards = Card.objects.filter(user=user, level='intermediate')
        intermediate_without_schedule = intermediate_cards.exclude(schedule__repetitions__gte=5)
        if intermediate_without_schedule.exists():
            recommendations.append({
                'type': 'intermediate',
                'message': f'Удели внимание {intermediate_without_schedule.count()} словам среднего уровня',
                'count': intermediate_without_schedule.count()
            })
        
        # Рекомендация по карточкам на сегодня
        if stats['today_cards'] > 0:
            recommendations.append({
                'type': 'today',
                'message': f'У тебя {stats["today_cards"]} карточек для повторения сегодня',
                'count': stats['today_cards']
            })
        
        # Рекомендация по низкому проценту успеха
        if stats['stats'].total_reviews > 10 and stats['success_rate'] < 60:
            recommendations.append({
                'type': 'low_success',
                'message': f'Процент правильных ответов низкий ({stats["success_rate"]}%). Больше практикуйся!',
                'count': 0
            })
        
        return recommendations

