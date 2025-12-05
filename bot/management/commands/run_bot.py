"""
Django management команда для запуска Telegram-бота.
"""
import asyncio
import os
import django
from django.core.management.base import BaseCommand

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'linguatrack.settings')
django.setup()

from bot.bot import main


class Command(BaseCommand):
    """Команда для запуска бота через manage.py"""
    help = 'Запускает Telegram-бота'
    
    def handle(self, *args, **options):
        """Запуск бота"""
        self.stdout.write(self.style.SUCCESS('Запуск Telegram-бота...'))
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Бот остановлен'))
