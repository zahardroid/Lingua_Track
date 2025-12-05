#!/usr/bin/env python
"""
Скрипт для запуска Telegram-бота.
Использование: python run_bot.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'linguatrack.settings')
django.setup()

from bot.bot import main
import asyncio

if __name__ == "__main__":
    print("Запуск Telegram-бота LinguaTrack...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот остановлен")

