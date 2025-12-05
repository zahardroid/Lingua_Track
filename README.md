# LinguaTrack

MVP-платформа для изучения иностранных слов с флеш-карточками, интервальным повторением и интеграцией с Telegram-ботом.

## Технологии

- **Backend**: Django 4.2
- **Frontend**: Django Templates + Bootstrap 5
- **База данных**: SQLite
- **Telegram-бот**: aiogram 3.1
- **Озвучка**: gTTS
- **Фоновая логика**: Celery + Redis

## Установка

1. Клонируйте репозиторий или создайте проект

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

4. Заполните `.env` файл:
- `SECRET_KEY` - секретный ключ Django
- `TELEGRAM_BOT_TOKEN` - токен вашего Telegram-бота (получите у @BotFather)
- `CELERY_BROKER_URL` - URL Redis для Celery
- `TTS_LANGUAGE` - язык для озвучки (по умолчанию 'en')

5. Примените миграции:
```bash
python manage.py migrate
```

6. Создайте суперпользователя:
```bash
python manage.py createsuperuser
```

## Запуск

### Django сервер
```bash
python manage.py runserver
```

### Celery worker
```bash
celery -A linguatrack worker -l info
```

### Celery beat (для периодических задач)
```bash
celery -A linguatrack beat -l info
```

### Telegram-бот
```bash
python manage.py run_bot
```

Или напрямую:
```bash
python -m bot.bot
```

## Основные функции

### Веб-интерфейс

- **CRUD карточек**: создание, просмотр, редактирование, удаление
- **Фильтрация**: по уровню сложности и поиск
- **Интервальное повторение**: алгоритм SM-2
- **Тестирование**: режим тестирования с оценкой качества ответа
- **Озвучка**: воспроизведение слов через gTTS
- **Статистика**: прогресс изучения, рекомендации

### Telegram-бот

Команды:
- `/start` - приветствие и список команд
- `/today` - карточки на сегодня
- `/test` - быстрый тест
- `/progress` - статистика
- `/cards` - список карточек
- `/say <слово>` - озвучка слова
- `/add <слово> | <перевод>` - добавить карточку

## Структура проекта

```
linguatrack/
├── manage.py
├── linguatrack/
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   └── __init__.py
├── cards/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── services.py
│   ├── tts.py
│   └── templates/
├── schedules/
│   ├── models.py
│   └── services.py
├── stats/
│   ├── models.py
│   ├── views.py
│   ├── services.py
│   └── templates/
├── bot/
│   ├── bot.py
│   └── tasks.py
└── templates/
```

## Алгоритм SM-2

Проект использует алгоритм SuperMemo 2 для интервального повторения:
- Качество ответа оценивается от 0 до 5
- Интервал повторения рассчитывается автоматически
- Фактор легкости корректируется на основе качества ответа

## Разработка

Для разработки рекомендуется использовать виртуальное окружение:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

## Лицензия

MIT

