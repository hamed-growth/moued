"""Admin autodiscovery for the installed model registry."""

from django.contrib import admin

ADMIN_GROUPS = [
    {
        'key': 'users',
        'name': 'اطلاعات کاربران و گروه‌ها',
        'icon': 'fa-users',
        'color': '#4338ca',
        'models': ['User', 'Group', 'Team', 'TeamMember', 'PointTransaction'],
    },
    {
        'key': 'questions',
        'name': 'سوالات',
        'icon': 'fa-circle-question',
        'color': '#0284c7',
        'models': ['Question', 'DailyQuestion', 'DailyQuestionAnswer'],
    },
    {
        'key': 'missions',
        'name': 'ماموریت‌ها',
        'icon': 'fa-list-check',
        'color': '#059669',
        'models': [
            'MissionCategory', 'Mission', 'TeamMission',
            'MissionRequest', 'MissionCompletion',
        ],
    },
    {
        'key': 'competitions',
        'name': 'مسابقات',
        'icon': 'fa-trophy',
        'color': '#d4a017',
        'models': [
            'Competition', 'CompetitionQuestion',
            'CompetitionRegistration', 'CompetitionAnswer',
        ],
    },
    {
        'key': 'treasure',
        'name': 'جوایز و صندوق گنج',
        'icon': 'fa-gift',
        'color': '#dc2626',
        'models': ['TreasureCategory', 'TreasureItem', 'TreasurePurchase'],
    },
]


def get_grouped_app_list(original_app_list):
    """مدل‌ها را در گروه‌های سفارشی مرتب می‌کند"""
    all_models = {}
    for app in original_app_list:
        for model in app['models']:
            all_models[model['object_name']] = model

    grouped_app_list = []

    for group in ADMIN_GROUPS:
        group_models = []
        for model_name in group['models']:
            if model_name in all_models:
                group_models.append(all_models[model_name])

        if group_models:
            grouped_app_list.append({
                'name': group['name'],
                'app_label': group['key'],
                'app_url': '',
                'has_module_perms': True,
                'models': group_models,
                'icon': group['icon'],
                'color': group['color'],
            })

    used_models = set()
    for group in ADMIN_GROUPS:
        used_models.update(group['models'])

    remaining = []
    for model_name, model in all_models.items():
        if model_name not in used_models:
            remaining.append(model)

    if remaining:
        grouped_app_list.append({
            'name': 'سایر',
            'app_label': 'other',
            'app_url': '',
            'has_module_perms': True,
            'models': remaining,
            'icon': 'fa-cube',
            'color': '#78716c',
        })

    return grouped_app_list


# =====================================================================
# 🔧 جایگزینی متد get_app_list در AdminSite
# =====================================================================

_original_get_app_list = admin.AdminSite.get_app_list


def _custom_get_app_list(self, request, app_label=None):
    original_list = _original_get_app_list(self, request, app_label)
    if app_label is None:
        return get_grouped_app_list(original_list)
    return original_list


admin.AdminSite.get_app_list = _custom_get_app_list

from apps.accounts import admin as accounts_admin  # noqa: E402, F401
from apps.teams import admin as teams_admin  # noqa: E402, F401
from apps.wallet import admin as wallet_admin  # noqa: E402, F401
from apps.missions import admin as missions_admin  # noqa: E402, F401
from apps.questions import admin as questions_admin  # noqa: E402, F401
from apps.competitions import admin as competitions_admin  # noqa: E402, F401
from apps.treasure import admin as treasure_admin  # noqa: E402, F401
