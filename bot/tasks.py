"""
Celery задачи для Telegram-бота.
"""
import logging
from celery import shared_task
from django.utils import timezone
from django.contrib.auth.models import User
from schedules.services import SM2Service
from stats.models import UserProfile

logger = logging.getLogger('bot')


@shared_task
def send_daily_reminders():
    """
    Отправляет напоминания пользователям о карточках на сегодня.
    """
    import asyncio
    from bot.bot import bot
    
    async def send_reminders():
        profiles = UserProfile.objects.filter(telegram_id__isnull=False)
        processed = 0
        sent = 0
        
        for profile in profiles:
            cards = SM2Service.get_cards_for_today(profile.user)
            if cards:
                try:
                    message = (
                        f"📚 Напоминание!\n\n"
                        f"У тебя {len(cards)} карточек для повторения сегодня.\n\n"
                        f"Используй /today чтобы посмотреть список или /test для быстрого теста!"
                    )
                    await bot.send_message(profile.telegram_id, message)
                    sent += 1
                except Exception as e:
                    logger.error(f"Ошибка отправки напоминания пользователю {profile.user.username}: {e}", exc_info=True)
                processed += 1
        
        return f"Processed {processed} users, sent {sent} reminders"
    
    # Запускаем асинхронную функцию
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(send_reminders())

