from django.urls import path
from apps.backoffice import staff_views as backoffice_staff_views
from apps.accounts import staff_views as accounts_staff_views
from apps.teams import staff_views as teams_staff_views
from apps.missions import staff_views as missions_staff_views
from apps.competitions import staff_views as competitions_staff_views
from apps.questions import staff_views as questions_staff_views
from apps.treasure import staff_views as treasure_staff_views
from apps.wallet import staff_views as wallet_staff_views

app_name = 'dashboard'

urlpatterns = [
    path('', backoffice_staff_views.home, name='home'),

    # کاربران
    path('users/', accounts_staff_views.users_list, name='users'),
    path('users/<int:user_id>/', accounts_staff_views.user_detail, name='user_detail'),
    path('users/<int:user_id>/toggle-staff/', accounts_staff_views.user_toggle_staff, name='user_toggle_staff'),
    path('users/<int:user_id>/toggle-manager/', accounts_staff_views.user_toggle_manager, name='user_toggle_manager'),
    path('users/<int:user_id>/toggle-active/', accounts_staff_views.user_toggle_active, name='user_toggle_active'),

    # تیم‌ها
    path('teams/', teams_staff_views.teams_list, name='teams'),
    path('teams/<int:team_id>/', teams_staff_views.team_detail, name='team_detail'),
    path('teams/<int:team_id>/missions/toggle/<int:mission_id>/',
         teams_staff_views.team_mission_toggle, name='team_mission_toggle'),

    # ماموریت‌ها
    path('missions/', missions_staff_views.missions_list, name='missions'),
    path('missions/requests/', missions_staff_views.mission_requests_list, name='mission_requests'),
    path('missions/requests/<int:req_id>/approve/', missions_staff_views.mission_request_approve, name='mission_request_approve'),
    path('missions/requests/<int:req_id>/reject/', missions_staff_views.mission_request_reject, name='mission_request_reject'),

    # مسابقات
    path('competitions/', competitions_staff_views.competitions_list, name='competitions'),
    path('competitions/<int:comp_id>/finalize/', competitions_staff_views.competition_finalize, name='competition_finalize'),

    # سوالات
    path('questions/', questions_staff_views.questions_list, name='questions'),
    path('daily-questions/', questions_staff_views.daily_questions_list, name='daily_questions'),

    # صندوق گنج
    path('treasure/', treasure_staff_views.treasure_list, name='treasure'),
    path('treasure/purchases/<int:purchase_id>/deliver/', treasure_staff_views.treasure_purchase_deliver, name='treasure_purchase_deliver'),
    path('treasure/purchases/<int:purchase_id>/reject/', treasure_staff_views.treasure_purchase_reject, name='treasure_purchase_reject'),

    # تراکنش‌ها
    path('transactions/', wallet_staff_views.transactions_list, name='transactions'),
]
