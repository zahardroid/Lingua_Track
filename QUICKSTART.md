# Быстрый старт LinguaTrack

## 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

## 2. Настройка окружения

Создайте файл `.env` в корне проекта:

```env
SECRET_KEY=django-insecure-your-secret-key-here
DEBUG=True
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TTS_LANGUAGE=en
```

## 3. Инициализация базы данных

```bash
python manage.py migrate
python manage.py createsuperuser
```

## 4. Запуск компонентов

### Django сервер (в отдельном терминале)
```bash
python manage.py runserver
```

### Celery worker (в отдельном терминале)
```bash
celery -A linguatrack worker -l info
```

### Celery beat (в отдельном терминале, опционально)
```bash
celery -A linguatrack beat -l info
```

### Telegram-бот (в отдельном терминале)
```bash
python manage.py run_bot
```
или
```bash
python run_bot.py
```

## 5. Использование

### Веб-интерфейс
Откройте браузер: http://127.0.0.1:8000

### Telegram-бот
Найдите вашего бота в Telegram и отправьте `/start`

## Команды Telegram-бота

- `/start` - приветствие
- `/today` - карточки на сегодня
- `/test` - быстрый тест
- `/progress` - статистика
- `/cards` - список карточек
- `/say hello` - озвучка слова
- `/add hello | привет` - добавить карточку

## Примечания

- Убедитесь, что Redis запущен для работы Celery
- Для получения токена бота обратитесь к @BotFather в Telegram
- Первый запуск может занять время из-за создания базы данных

