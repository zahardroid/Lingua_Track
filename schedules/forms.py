from django import forms
from .models import Schedule


class ScheduleUpdateForm(forms.ModelForm):
    """Форма для ручного изменения даты следующего повторения."""
    
    class Meta:
        model = Schedule
        fields = ['next_review_at']
        widgets = {
            'next_review_at': forms.DateTimeInput(
                attrs={
                    'class': 'form-control',
                    'type': 'datetime-local'
                },
                format='%Y-%m-%dT%H:%M'
            ),
        }
        labels = {
            'next_review_at': 'Следующее повторение',
        }

