from django.urls import path
from . import views

app_name = 'missions'

urlpatterns = [
    # ============ عمومی ============
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # ============ ماموریت‌ها ============
    path('missions/<int:mission_id>/request/', views.request_mission, name='request_mission'),

    # ============ سوالات روزانه ============
    path('daily/', views.daily_questions_page, name='daily_questions'),
    path('daily/<int:dq_id>/answer/', views.answer_daily, name='answer_daily'),

    # ============ مسابقات (یکپارچه) ============
    path('competitions/', views.competition_list, name='competition_list'),
    path('competitions/<int:competition_id>/', views.competition_detail, name='competition_detail'),
    path('competitions/<int:competition_id>/register/', views.register_competition, name='register_competition'),
    path('competitions/<int:competition_id>/questions/<int:question_id>/answer/', views.submit_answer, name='submit_answer'),
    path('competitions/<int:competition_id>/finish/', views.finish_competition, name='finish_competition'),
    path('competitions/<int:competition_id>/play/', views.competition_play, name='competition_play'),
    path('competitions/<int:competition_id>/start/', views.start_competition, name='start_competition'),


    # ============ پروفایل ============
    path('profile/', views.profile, name='profile'),

    # ============ صندوق گنج ============
    path('treasure/', views.treasure_box, name='treasure_box'),
    path('treasure/buy/<int:item_id>/', views.buy_treasure_item, name='buy_treasure_item'),

    # ============ مسیرهای فوتر ============
    path('treasure/', views.treasure_box, name='treasure_box'),
    path('archive/', views.archive, name='archive'),
    path('leagues/', views.league_list, name='league_list'),
]