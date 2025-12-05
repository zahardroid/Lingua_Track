from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .services import StatsService


@login_required
def progress(request):
    """Страница прогресса и статистики."""
    stats_data = StatsService.get_user_stats(request.user)
    recommendations = StatsService.get_recommendations(request.user)
    
    context = {
        **stats_data,
        'recommendations': recommendations,
    }
    
    return render(request, 'stats/progress.html', context)

