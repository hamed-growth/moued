from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home, name='home'),

    # کاربران
    path('users/', views.users_list, name='users'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/toggle-staff/', views.user_toggle_staff, name='user_toggle_staff'),
    path('users/<int:user_id>/toggle-manager/', views.user_toggle_manager, name='user_toggle_manager'),
    path('users/<int:user_id>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),

    # تیم‌ها
    path('teams/', views.teams_list, name='teams'),
    path('teams/<int:team_id>/', views.team_detail, name='team_detail'),
    path('teams/<int:team_id>/missions/toggle/<int:mission_id>/',
         views.team_mission_toggle, name='team_mission_toggle'),

    # ماموریت‌ها
    path('missions/', views.missions_list, name='missions'),
    path('missions/requests/', views.mission_requests_list, name='mission_requests'),
    path('missions/requests/<int:req_id>/approve/', views.mission_request_approve, name='mission_request_approve'),
    path('missions/requests/<int:req_id>/reject/', views.mission_request_reject, name='mission_request_reject'),

    # مسابقات
    path('competitions/', views.competitions_list, name='competitions'),
    path('competitions/<int:comp_id>/finalize/', views.competition_finalize, name='competition_finalize'),

    # سوالات
    path('questions/', views.questions_list, name='questions'),
    path('daily-questions/', views.daily_questions_list, name='daily_questions'),

    # صندوق گنج
    path('treasure/', views.treasure_list, name='treasure'),
    path('treasure/purchases/<int:purchase_id>/deliver/', views.treasure_purchase_deliver, name='treasure_purchase_deliver'),

    # تراکنش‌ها
    path('transactions/', views.transactions_list, name='transactions'),
]