from django.urls import path
from . import auth_views, views, mission_views

app_name = "api_v1"

urlpatterns = [
    path("missions/calendar/", mission_views.MissionCalendarView.as_view(), name="mission_calendar"),
    path("missions/<int:mission_id>/requests/", mission_views.MissionSubmitView.as_view(), name="mission_submit"),
    path("staff/mission-requests/", mission_views.StaffMissionRequestsView.as_view(), name="staff_mission_requests"),
    path("staff/mission-requests/<int:request_id>/review/", mission_views.MissionReviewView.as_view(), name="mission_review"),
    path("auth/csrf/", auth_views.csrf_cookie, name="csrf"),
    path("auth/login/", auth_views.session_login, name="login"),
    path("auth/register/", auth_views.session_register, name="register"),
    path("auth/logout/", auth_views.session_logout, name="logout"),
    path("me/", views.MeView.as_view(), name="me"),
    path("me/wallet/", views.WalletView.as_view(), name="wallet"),
    path("me/transactions/", views.MyTransactionList.as_view(), name="transactions"),
    path("me/mission-requests/", views.MyMissionRequestList.as_view(), name="mission_requests"),
    path("missions/", views.MissionList.as_view(), name="missions"),
    path("treasure/items/", views.TreasureCatalogList.as_view(), name="treasure_items"),
]
