from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.conf import settings
from django.views.decorators.http import require_http_methods
from pathlib import Path
import json
import csv
import logging
from .models import Card
from .forms import CardForm
from .services import CardService
from .tts import TTSService
from schedules.services import SM2Service
from schedules.forms import ScheduleUpdateForm
from stats.models import Stats

logger = logging.getLogger('cards')


@login_required
def card_list(request):
    """Список карточек пользователя."""
    level_filter = request.GET.get('level', '')
    search_query = request.GET.get('search', '')
    
    cards = CardService.get_user_cards(request.user, level=level_filter if level_filter else None)
    
    if search_query:
        cards = cards.filter(
            Q(word__icontains=search_query) | Q(translation__icontains=search_query)
        )
    
    paginator = Paginator(cards, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'level_filter': level_filter,
        'search_query': search_query,
    }
    return render(request, 'cards/card_list.html', context)


@login_required
def card_detail(request, pk):
    """Детальный просмотр карточки."""
    card = get_object_or_404(Card, pk=pk, user=request.user)
    schedule = getattr(card, 'schedule', None)
    
    context = {
        'card': card,
        'schedule': schedule,
    }
    return render(request, 'cards/card_detail.html', context)


@login_required
def card_create(request):
    """Создание новой карточки."""
    if request.method == 'POST':
        form = CardForm(request.POST)
        form.user = request.user  # Передаем пользователя для валидации
        if form.is_valid():
            try:
                card = CardService.create_card(
                    user=request.user,
                    word=form.cleaned_data['word'],
                    translation=form.cleaned_data['translation'],
                    example=form.cleaned_data.get('example'),
                    note=form.cleaned_data.get('note'),
                    level=form.cleaned_data['level']
                )
                messages.success(request, f'Карточка "{card.word}" успешно создана!')
                return redirect('cards:card_detail', pk=card.pk)
            except Exception as e:
                messages.error(request, f'Ошибка при создании карточки: {str(e)}')
    else:
        form = CardForm()
        form.user = request.user
    
    return render(request, 'cards/card_form.html', {'form': form, 'action': 'Создать'})


@login_required
def card_update(request, pk):
    """Редактирование карточки."""
    card = get_object_or_404(Card, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = CardForm(request.POST, instance=card)
        if form.is_valid():
            form.save()
            messages.success(request, f'Карточка "{card.word}" успешно обновлена!')
            return redirect('cards:card_detail', pk=card.pk)
    else:
        form = CardForm(instance=card)
    
    return render(request, 'cards/card_form.html', {'form': form, 'card': card, 'action': 'Редактировать'})


@login_required
def card_delete(request, pk):
    """Удаление карточки."""
    card = get_object_or_404(Card, pk=pk, user=request.user)
    
    if request.method == 'POST':
        word = card.word
        CardService.delete_card(card)
        messages.success(request, f'Карточка "{word}" удалена!')
        return redirect('cards:card_list')
    
    return render(request, 'cards/card_confirm_delete.html', {'card': card})


@login_required
def today_cards(request):
    """Карточки для повторения сегодня."""
    cards = SM2Service.get_cards_for_today(request.user)
    
    context = {
        'cards': cards,
        'count': len(cards),
    }
    return render(request, 'cards/today_cards.html', context)


@login_required
def test_mode(request, pk=None):
    """Режим тестирования."""
    if pk:
        # Тест одной карточки
        card = get_object_or_404(Card, pk=pk, user=request.user)
        context = {'card': card, 'single': True}
        return render(request, 'cards/test_mode.html', context)
    else:
        # Тест карточек на сегодня
        cards = SM2Service.get_cards_for_today(request.user)
        if not cards:
            messages.info(request, 'Нет карточек для повторения сегодня!')
            return redirect('cards:card_list')
        
        card = cards[0]  # Берем первую карточку
        context = {
            'card': card,
            'remaining': len(cards) - 1,
            'single': False,
        }
        return render(request, 'cards/test_mode.html', context)


@login_required
def submit_answer(request, pk):
    """Обработка ответа в тесте."""
    card = get_object_or_404(Card, pk=pk, user=request.user)
    
    if request.method == 'POST':
        quality = int(request.POST.get('quality', 3))
        quality = max(0, min(5, quality))  # Ограничиваем 0-5
        
        # Обновляем расписание
        SM2Service.update_schedule(card, quality)
        
        # Обновляем статистику
        stats, _ = Stats.objects.get_or_create(user=request.user)
        stats.total_reviews += 1
        if quality < 3:
            stats.wrong_answers += 1
        stats.last_review_date = card.schedule.last_reviewed_at
        stats.save()
        
        messages.success(request, 'Ответ сохранен!')
        
        # Получаем следующую карточку
        cards = SM2Service.get_cards_for_today(request.user)
        if cards:
            return redirect('cards:test_mode', pk=cards[0].pk)
        else:
            messages.info(request, 'Все карточки на сегодня пройдены!')
            return redirect('cards:today_cards')
    
    return redirect('cards:test_mode', pk=pk)


@login_required
def say_word(request, word):
    """Озвучивание слова через TTS."""
    try:
        audio_path = TTSService.generate_audio(word)
        if audio_path.exists():
            return FileResponse(
                open(audio_path, 'rb'),
                content_type='audio/mpeg',
                filename=audio_path.name
            )
        else:
            raise Http404("Audio file not found")
    except Exception as e:
        raise Http404(f"Error generating audio: {str(e)}")


@login_required
def update_schedule(request, pk):
    """Ручное изменение даты следующего повторения."""
    card = get_object_or_404(Card, pk=pk, user=request.user)
    schedule = getattr(card, 'schedule', None)
    
    if not schedule:
        messages.error(request, 'Расписание для этой карточки не найдено')
        return redirect('cards:card_detail', pk=pk)
    
    if request.method == 'POST':
        form = ScheduleUpdateForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Дата следующего повторения обновлена!')
            return redirect('cards:card_detail', pk=pk)
    else:
        form = ScheduleUpdateForm(instance=schedule)
    
    return render(request, 'schedules/update_schedule.html', {
        'form': form,
        'card': card,
        'schedule': schedule
    })


@login_required
def test_multiple_choice(request, pk=None):
    """Режим тестирования с множественным выбором."""
    if pk:
        card = get_object_or_404(Card, pk=pk, user=request.user)
        cards_for_choices = list(Card.objects.filter(user=request.user).exclude(pk=pk).order_by('?')[:3])
        cards_for_choices.append(card)
        import random
        random.shuffle(cards_for_choices)
        
        context = {
            'card': card,
            'choices': cards_for_choices,
            'single': True
        }
        return render(request, 'cards/test_multiple_choice.html', context)
    else:
        cards = SM2Service.get_cards_for_today(request.user)
        if not cards:
            messages.info(request, 'Нет карточек для повторения сегодня!')
            return redirect('cards:card_list')
        
        card = cards[0]
        cards_for_choices = list(Card.objects.filter(user=request.user).exclude(pk=card.pk).order_by('?')[:3])
        cards_for_choices.append(card)
        import random
        random.shuffle(cards_for_choices)
        
        context = {
            'card': card,
            'choices': cards_for_choices,
            'remaining': len(cards) - 1,
            'single': False
        }
        return render(request, 'cards/test_multiple_choice.html', context)


@login_required
def test_matching(request):
    """Режим тестирования - сопоставление слов и переводов."""
    cards = list(Card.objects.filter(user=request.user).order_by('?')[:8])
    
    if len(cards) < 4:
        messages.info(request, 'Нужно минимум 4 карточки для режима сопоставления!')
        return redirect('cards:card_list')
    
    words = [card.word for card in cards]
    translations = [card.translation for card in cards]
    import random
    random.shuffle(translations)
    
    context = {
        'words': words,
        'translations': translations,
        'cards': cards
    }
    return render(request, 'cards/test_matching.html', context)


@login_required
@require_http_methods(["POST"])
def submit_matching(request):
    """Обработка ответа в режиме сопоставления."""
    data = json.loads(request.body)
    matches = data.get('matches', {})
    
    correct = 0
    total = len(matches)
    
    for word, translation in matches.items():
        try:
            card = Card.objects.get(user=request.user, word=word)
            if card.translation == translation:
                correct += 1
                # Обновляем расписание для правильных ответов
                SM2Service.update_schedule(card, 5)
            else:
                # Обновляем для неправильных
                SM2Service.update_schedule(card, 0)
        except Card.DoesNotExist:
            pass
    
    # Обновляем статистику
    stats, _ = Stats.objects.get_or_create(user=request.user)
    stats.total_reviews += total
    stats.wrong_answers += (total - correct)
    stats.save()
    
    return JsonResponse({
        'correct': correct,
        'total': total,
        'percentage': round((correct / total) * 100, 2) if total > 0 else 0
    })


@login_required
def export_cards(request):
    """Экспорт карточек в CSV."""
    cards = Card.objects.filter(user=request.user)
    
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="cards_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Слово', 'Перевод', 'Пример', 'Заметка', 'Уровень', 'Создано'])
    
    for card in cards:
        writer.writerow([
            card.word,
            card.translation,
            card.example or '',
            card.note or '',
            card.get_level_display(),
            card.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response


@login_required
def import_cards(request):
    """Импорт карточек из CSV."""
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        try:
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            
            imported = 0
            errors = []
            
            # Маппинг уровней
            level_mapping = {
                'начальный': 'beginner',
                'средний': 'intermediate',
                'продвинутый': 'advanced',
                'beginner': 'beginner',
                'intermediate': 'intermediate',
                'advanced': 'advanced',
            }
            
            for row in reader:
                try:
                    level_str = row.get('Уровень', 'beginner').strip().lower()
                    level = level_mapping.get(level_str, 'beginner')
                    
                    CardService.create_card(
                        user=request.user,
                        word=row.get('Слово', '').strip(),
                        translation=row.get('Перевод', '').strip(),
                        example=row.get('Пример', '').strip() or None,
                        note=row.get('Заметка', '').strip() or None,
                        level=level
                    )
                    imported += 1
                except Exception as e:
                    errors.append(f"Ошибка в строке: {str(e)}")
            
            messages.success(request, f'Импортировано {imported} карточек!')
            if errors:
                messages.warning(request, f'Ошибок: {len(errors)}')
            
            return redirect('cards:card_list')
        except Exception as e:
            messages.error(request, f'Ошибка импорта: {str(e)}')
    
    return render(request, 'cards/import_cards.html')

