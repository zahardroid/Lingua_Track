from django.contrib import admin
from .models import Card


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ['word', 'translation', 'level', 'user', 'created_at']
    list_filter = ['level', 'created_at']
    search_fields = ['word', 'translation']
    readonly_fields = ['created_at', 'updated_at']

