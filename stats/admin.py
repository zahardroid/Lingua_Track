from django.contrib import admin
from .models import Stats, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'telegram_id', 'telegram_username', 'created_at']
    search_fields = ['user__username', 'telegram_username', 'telegram_id']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Stats)
class StatsAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_words', 'learned_words', 'total_reviews', 'success_rate']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at', 'success_rate']

