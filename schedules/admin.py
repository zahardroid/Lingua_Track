from django.contrib import admin
from .models import Schedule


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['card', 'next_review_at', 'interval', 'repetitions', 'easiness_factor']
    list_filter = ['next_review_at']
    search_fields = ['card__word', 'card__translation']
    readonly_fields = ['last_reviewed_at']

