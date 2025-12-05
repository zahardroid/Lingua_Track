from django import forms
from django.core.exceptions import ValidationError
from .models import Card


class CardForm(forms.ModelForm):
    """Форма для создания и редактирования карточек."""
    
    class Meta:
        model = Card
        fields = ['word', 'translation', 'example', 'note', 'level']
        widgets = {
            'word': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите слово',
                'maxlength': '200'
            }),
            'translation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите перевод',
                'maxlength': '200'
            }),
            'example': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Пример использования (необязательно)'
            }),
            'note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Заметка (необязательно)'
            }),
            'level': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'word': 'Слово',
            'translation': 'Перевод',
            'example': 'Пример',
            'note': 'Заметка',
            'level': 'Уровень',
        }
    
    def clean_word(self):
        word = self.cleaned_data.get('word', '').strip()
        if not word:
            raise ValidationError('Слово не может быть пустым')
        if len(word) > 200:
            raise ValidationError('Слово не может быть длиннее 200 символов')
        return word
    
    def clean_translation(self):
        translation = self.cleaned_data.get('translation', '').strip()
        if not translation:
            raise ValidationError('Перевод не может быть пустым')
        if len(translation) > 200:
            raise ValidationError('Перевод не может быть длиннее 200 символов')
        return translation
    
    def clean(self):
        cleaned_data = super().clean()
        word = cleaned_data.get('word', '').strip()
        translation = cleaned_data.get('translation', '').strip()
        
        # Проверка на дубликаты (только при создании новой карточки)
        if self.instance.pk is None and word and translation:
            user = getattr(self, 'user', None)
            if user:
                existing = Card.objects.filter(
                    user=user,
                    word__iexact=word,
                    translation__iexact=translation
                ).exists()
                if existing:
                    raise ValidationError(
                        'Карточка с таким словом и переводом уже существует'
                    )
        
        return cleaned_data

