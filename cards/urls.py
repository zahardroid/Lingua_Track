from django.urls import path
from . import views
from . import views_auth

app_name = 'cards'

urlpatterns = [
    path('login/', views_auth.login_view, name='login'),
    path('logout/', views_auth.logout_view, name='logout'),
    path('', views.card_list, name='card_list'),
    path('create/', views.card_create, name='card_create'),
    path('<int:pk>/', views.card_detail, name='card_detail'),
    path('<int:pk>/edit/', views.card_update, name='card_update'),
    path('<int:pk>/delete/', views.card_delete, name='card_delete'),
    path('today/', views.today_cards, name='today_cards'),
    path('test/', views.test_mode, name='test_mode'),
    path('test/<int:pk>/', views.test_mode, name='test_mode'),
    path('test/<int:pk>/submit/', views.submit_answer, name='submit_answer'),
    path('say/<str:word>/', views.say_word, name='say_word'),
    path('<int:pk>/schedule/', views.update_schedule, name='update_schedule'),
    path('test/multiple/', views.test_multiple_choice, name='test_multiple_choice'),
    path('test/multiple/<int:pk>/', views.test_multiple_choice, name='test_multiple_choice'),
    path('test/matching/', views.test_matching, name='test_matching'),
    path('test/matching/submit/', views.submit_matching, name='submit_matching'),
    path('export/', views.export_cards, name='export_cards'),
    path('import/', views.import_cards, name='import_cards'),
]

