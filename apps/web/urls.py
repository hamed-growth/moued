from django.urls import path

from apps.accounts import views as accounts_views
from apps.web import views as web_views
from apps.web import mission_views
from apps.missions import views as mission_actions

app_name = 'missions'

urlpatterns = [
    path('', accounts_views.login_view, name='home'),
    path('login/', accounts_views.login_view, name='login'),
    path('register/', accounts_views.register_view, name='register'),
    path('missions/', mission_views.missions_page, name='mission_list'),
    path('missions/days/', mission_views.mission_days, name='mission_days'),
    path('missions/<int:mission_id>/request/', mission_actions.request_mission, name='request_mission'),
    path('dashboard/', web_views.dashboard, name='dashboard'),
    path('logout/', accounts_views.logout_view, name='logout'),
]
