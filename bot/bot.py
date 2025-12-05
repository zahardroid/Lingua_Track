"""
Telegram-бот для LinguaTrack на aiogram.
"""
import os
import asyncio
import django
import logging

# Настройка Django перед импортом моделей
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'linguatrack.settings')
django.setup()

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from django.conf import settings
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async
from cards.models import Card
from cards.services import CardService
from cards.tts import TTSService
from schedules.services import SM2Service
from stats.services import StatsService
from stats.models import Stats, UserProfile

logger = logging.getLogger('bot')


# Инициализация бота
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# Состояния для FSM
class AddCardState(StatesGroup):
    waiting_for_card = State()


class SayWordState(StatesGroup):
    waiting_for_word = State()


# Создаем клавиатуру с основными кнопками
def get_main_keyboard():
    """Создает основную клавиатуру с кнопками."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📚 Карточки на сегодня"),
                KeyboardButton(text="🧪 Тест")
            ],
            [
                KeyboardButton(text="📊 Статистика"),
                KeyboardButton(text="📝 Мои карточки")
            ],
            [
                KeyboardButton(text="➕ Добавить карточку"),
                KeyboardButton(text="🔊 Озвучить слово")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )
    return keyboard


@sync_to_async
def get_or_create_user(telegram_id: int, username: str = None) -> User:
    """
    Получает или создает пользователя Django по Telegram ID.
    
    Args:
        telegram_id: ID пользователя в Telegram
        username: Имя пользователя в Telegram
    
    Returns:
        User: Пользователь Django
    """
    try:
        profile = UserProfile.objects.get(telegram_id=telegram_id)
        user = profile.user
    except UserProfile.DoesNotExist:
        # Создаем пользователя
        user = User.objects.create_user(
            username=f"tg_{telegram_id}",
            email=f"tg_{telegram_id}@telegram.local",
            password=None
        )
        user.first_name = username or f"User_{telegram_id}"
        user.save()
        
        # Создаем профиль с telegram_id
        UserProfile.objects.create(
            user=user,
            telegram_id=telegram_id,
            telegram_username=username
        )
    
    return user


@sync_to_async
def get_cards_for_today(user):
    """Получить карточки на сегодня."""
    return SM2Service.get_cards_for_today(user)


@sync_to_async
def get_card_by_id(card_id):
    """Получить карточку по ID."""
    return Card.objects.get(pk=card_id)


@sync_to_async
def update_card_schedule(card, quality):
    """Обновить расписание карточки."""
    return SM2Service.update_schedule(card, quality)


@sync_to_async
def get_or_create_stats(user):
    """Получить или создать статистику."""
    return Stats.objects.get_or_create(user=user)


@sync_to_async
def save_stats(stats):
    """Сохранить статистику."""
    stats.save()


@sync_to_async
def get_user_cards(user, limit=10):
    """Получить карточки пользователя."""
    return list(CardService.get_user_cards(user)[:limit])


@sync_to_async
def get_user_cards_count(user):
    """Получить количество карточек пользователя."""
    return Card.objects.filter(user=user).count()


@sync_to_async
def create_card(user, word, translation):
    """Создать карточку."""
    try:
        card = CardService.create_card(user, word, translation)
        # Принудительно обновляем объект из БД
        card.refresh_from_db()
        return card
    except Exception as e:
        logger.error(f"Error in create_card: {e}", exc_info=True)
        raise


@sync_to_async
def get_user_stats_data(user):
    """Получить статистику пользователя."""
    return StatsService.get_user_stats(user)


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Команда /start"""
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Я бот LinguaTrack для изучения иностранных слов.\n\n"
        "Используй кнопки ниже для навигации:",
        reply_markup=get_main_keyboard()
    )


@dp.message(Command("today"))
async def cmd_today(message: Message):
    """Команда /today - карточки на сегодня"""
    user = await get_or_create_user(message.from_user.id)
    cards = await get_cards_for_today(user)
    
    if not cards:
        await message.answer(
            "🎉 Отлично! У тебя нет карточек для повторения сегодня.",
            reply_markup=get_main_keyboard()
        )
        return
    
    text = f"📚 Карточки на сегодня ({len(cards)}):\n\n"
    for i, card in enumerate(cards[:10], 1):  # Показываем первые 10
        text += f"{i}. {card.word} - {card.translation}\n"
    
    if len(cards) > 10:
        text += f"\n... и еще {len(cards) - 10} карточек"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧪 Начать тест", callback_data="test_start")]
    ])
    
    await message.answer(text, reply_markup=keyboard)


@dp.message(lambda m: m.text == "🧪 Тест")
async def button_test(message: Message):
    """Обработка кнопки 'Тест'"""
    await cmd_test(message)


@dp.message(Command("test"))
async def cmd_test(message: Message):
    """Команда /test - быстрый тест"""
    user = await get_or_create_user(message.from_user.id)
    cards = await get_cards_for_today(user)
    
    if not cards:
        await message.answer(
            "Нет карточек для тестирования. Добавь карточки через кнопку '➕ Добавить карточку'",
            reply_markup=get_main_keyboard()
        )
        return
    
    card = cards[0]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👁 Показать ответ", callback_data=f"test_show_{card.pk}")]
    ])
    
    await message.answer(
        f"❓ Как переводится слово:\n\n<b>{card.word}</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@dp.callback_query(lambda c: c.data.startswith("test_show_"))
async def test_show_answer(callback: CallbackQuery):
    """Показать ответ в тесте"""
    card_id = int(callback.data.split("_")[-1])
    card = await get_card_by_id(card_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❌ 0", callback_data=f"quality_{card_id}_0"),
            InlineKeyboardButton(text="⚠️ 1", callback_data=f"quality_{card_id}_1"),
        ],
        [
            InlineKeyboardButton(text="✅ 3", callback_data=f"quality_{card_id}_3"),
            InlineKeyboardButton(text="🌟 5", callback_data=f"quality_{card_id}_5"),
        ]
    ])
    
    text = f"<b>{card.word}</b> = {card.translation}\n\n"
    if card.example:
        text += f"Пример: {card.example}\n\n"
    text += "Насколько хорошо ты знал это слово?"
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("quality_"))
async def test_submit_quality(callback: CallbackQuery):
    """Обработка качества ответа"""
    parts = callback.data.split("_")
    card_id = int(parts[1])
    quality = int(parts[2])
    
    card = await get_card_by_id(card_id)
    user = await get_or_create_user(callback.from_user.id)
    
    # Обновляем расписание
    await update_card_schedule(card, quality)
    
    # Обновляем статистику
    stats, _ = await get_or_create_stats(user)
    stats.total_reviews += 1
    if quality < 3:
        stats.wrong_answers += 1
    await save_stats(stats)
    
    # Получаем следующую карточку
    cards = await get_cards_for_today(user)
    if cards:
        next_card = cards[0]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👁 Показать ответ", callback_data=f"test_show_{next_card.pk}")]
        ])
        await callback.message.edit_text(
            f"✅ Ответ сохранен!\n\n❓ Следующее слово:\n\n<b>{next_card.word}</b>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text("🎉 Все карточки на сегодня пройдены!")
    
    await callback.answer("Ответ сохранен!")


@dp.callback_query(lambda c: c.data == "test_start")
async def test_start_callback(callback: CallbackQuery):
    """Начать тест из кнопки"""
    await cmd_test(callback.message)
    await callback.answer()


@dp.message(lambda m: m.text == "📊 Статистика")
async def button_progress(message: Message):
    """Обработка кнопки 'Статистика'"""
    await cmd_progress(message)


@dp.message(Command("progress"))
async def cmd_progress(message: Message):
    """Команда /progress - статистика"""
    user = await get_or_create_user(message.from_user.id)
    stats_data = await get_user_stats_data(user)
    stats = stats_data['stats']
    
    text = (
        f"📊 <b>Твоя статистика:</b>\n\n"
        f"📝 Всего слов: {stats.total_words}\n"
        f"✅ Изучено: {stats.learned_words}\n"
        f"🔄 Повторений: {stats.total_reviews}\n"
        f"❌ Ошибок: {stats.wrong_answers}\n"
        f"📈 Успешность: {stats_data['success_rate']}%\n"
        f"📅 На сегодня: {stats_data['today_cards']} карточек"
    )
    
    await message.answer(text, parse_mode="HTML", reply_markup=get_main_keyboard())


@dp.message(lambda m: m.text == "📝 Мои карточки")
async def button_cards(message: Message):
    """Обработка кнопки 'Мои карточки'"""
    await cmd_cards(message)


@dp.message(Command("cards"))
async def cmd_cards(message: Message):
    """Команда /cards - список карточек"""
    user = await get_or_create_user(message.from_user.id)
    cards = await get_user_cards(user, limit=10)
    
    if not cards:
        await message.answer(
            "У тебя пока нет карточек. Добавь через кнопку '➕ Добавить карточку'",
            reply_markup=get_main_keyboard()
        )
        return
    
    text = "📚 Твои карточки:\n\n"
    for i, card in enumerate(cards, 1):
        text += f"{i}. {card.word} - {card.translation} [{card.get_level_display()}]\n"
    
    total_count = await get_user_cards_count(user)
    if total_count > 10:
        text += f"\n... и еще {total_count - 10} карточек"
    
    await message.answer(text, reply_markup=get_main_keyboard())


@dp.message(lambda m: m.text and m.text.startswith("🔊 Озвучить слово"))
async def button_say_prompt(message: Message, state: FSMContext):
    """Обработка кнопки 'Озвучить слово' - запрос слова"""
    await state.set_state(SayWordState.waiting_for_word)
    await message.answer(
        "Напиши слово, которое хочешь озвучить:",
        reply_markup=ReplyKeyboardRemove()
    )


@dp.message(Command("say"))
async def cmd_say(message: Message):
    """Команда /say <слово> - озвучка"""
    word = message.text.replace("/say", "").strip()
    
    if not word:
        await message.answer("Использование: /say <слово>", reply_markup=get_main_keyboard())
        return
    
    await process_say_word(message, word)


async def process_say_word(message: Message, word: str):
    """Обработка озвучки слова"""
    
    try:
        audio_path = TTSService.generate_audio(word)
        if audio_path.exists():
            await message.answer_voice(voice=types.FSInputFile(audio_path))
            await message.answer(f"✅ Слово '{word}' озвучено!", reply_markup=get_main_keyboard())
        else:
            await message.answer("Не удалось создать аудио", reply_markup=get_main_keyboard())
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}", reply_markup=get_main_keyboard())


@dp.message(SayWordState.waiting_for_word)
async def handle_say_word_state(message: Message, state: FSMContext):
    """Обработка слова для озвучки в состоянии ожидания"""
    word = message.text.strip()
    await state.clear()
    
    if len(word.split()) == 1:  # Если одно слово
        await process_say_word(message, word)
    else:
        await message.answer(
            "Пожалуйста, отправь одно слово для озвучки.",
            reply_markup=get_main_keyboard()
        )


@dp.message(lambda m: m.text and not m.text.startswith("/") and not any([
    m.text == "📚 Карточки на сегодня",
    m.text == "🧪 Тест",
    m.text == "📊 Статистика",
    m.text == "📝 Мои карточки",
    m.text == "➕ Добавить карточку",
    m.text == "🔊 Озвучить слово",
]) and "|" not in m.text and "/" not in m.text)
async def handle_say_word(message: Message, state: FSMContext):
    """Обработка текстового сообщения как слова для озвучки (fallback)"""
    # Проверяем, не находимся ли мы в состоянии добавления карточки
    current_state = await state.get_state()
    if current_state == AddCardState.waiting_for_card.state:
        logger.debug(f"handle_say_word пропущен, т.к. в состоянии AddCardState")
        return
    
    word = message.text.strip()
    if len(word.split()) == 1:  # Если одно слово
        await process_say_word(message, word)
    else:
        await message.answer(
            "Пожалуйста, отправь одно слово для озвучки или используй кнопки.",
            reply_markup=get_main_keyboard()
        )


@dp.message(lambda m: m.text == "➕ Добавить карточку")
async def button_add_prompt(message: Message, state: FSMContext):
    """Обработка кнопки 'Добавить карточку' - запрос данных"""
    logger.debug(f"button_add_prompt вызван, устанавливаем состояние для user {message.from_user.id}")
    await state.set_state(AddCardState.waiting_for_card)
    current_state = await state.get_state()
    logger.debug(f"Текущее состояние после установки: {current_state}")
    await message.answer(
        "Отправь карточку в формате:\n"
        "<b>слово | перевод</b> или <b>слово / перевод</b>\n\n"
        "Пример: <code>hello | привет</code> или <code>hello / привет</code>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )


# Обработчик с состоянием должен быть ПЕРЕД общими обработчиками
@dp.message(AddCardState.waiting_for_card)
async def handle_add_card_state(message: Message, state: FSMContext):
    """Обработка добавления карточки в состоянии ожидания"""
    logger.debug(f"handle_add_card_state вызван с текстом: {message.text}")
    await state.clear()
    await process_add_card(message, message.text)


@dp.message(Command("add"))
async def cmd_add(message: Message):
    """Команда /add <слово> | <перевод> - добавить карточку"""
    text = message.text.replace("/add", "").strip()
    await process_add_card(message, text)


async def process_add_card(message: Message, text: str):
    """Обработка добавления карточки"""
    logger.debug(f"process_add_card вызван с текстом: {text}")
    # Поддерживаем оба разделителя: | и /
    separator = "|" if "|" in text else "/" if "/" in text else None
    
    if not separator:
        await message.answer(
            "Неверный формат! Используй:\n"
            "<b>слово | перевод</b> или <b>слово / перевод</b>\n\n"
            "Пример: <code>hello | привет</code> или <code>hello / привет</code>",
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )
        return
    
    parts = text.split(separator, 1)
    logger.debug(f"Разделитель: {separator}, Части: {parts}")
    if len(parts) != 2:
        await message.answer(
            "Неверный формат! Используй:\n"
            "<b>слово | перевод</b>",
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )
        return
    
    word = parts[0].strip()
    translation = parts[1].strip()
    
    if not word or not translation:
        await message.answer(
            "Слово и перевод не могут быть пустыми!",
            reply_markup=get_main_keyboard()
        )
        return
    
    try:
        logger.debug(f"Создаем карточку: word={word}, translation={translation}")
        user = await get_or_create_user(message.from_user.id)
        logger.debug(f"Пользователь получен: {user.username}")
        card = await create_card(user, word, translation)
        logger.debug(f"Карточка создана: {card.pk if card else None}")
        
        # Проверяем, что карточка действительно создана
        if card and card.pk:
            await message.answer(
                f"✅ Карточка добавлена!\n\n"
                f"<b>{card.word}</b> - {card.translation}",
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer(
                "❌ Карточка не была создана. Попробуйте еще раз.",
                reply_markup=get_main_keyboard()
            )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Ошибка при создании карточки: {error_msg}", exc_info=True)
        await message.answer(
            f"❌ Ошибка при добавлении карточки: {error_msg}\n\n"
            f"Попробуйте еще раз или обратитесь к администратору.",
            reply_markup=get_main_keyboard()
        )


# Fallback обработчик для добавления карточки (если пользователь не в состоянии, но ввел правильный формат)
@dp.message(lambda m: m.text and ("|" in m.text or "/" in m.text) and not m.text.startswith("/") and not any([
    m.text == "📚 Карточки на сегодня",
    m.text == "🧪 Тест",
    m.text == "📊 Статистика",
    m.text == "📝 Мои карточки",
    m.text == "➕ Добавить карточку",
    m.text == "🔊 Озвучить слово",
]))
async def handle_add_card(message: Message):
    """Обработка текстового сообщения с форматом 'слово | перевод' или 'слово / перевод' (fallback)"""
    await process_add_card(message, message.text)


async def main():
    """Запуск бота"""
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

