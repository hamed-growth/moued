"""Transport characterization for safe read-side extraction."""
import json
import os
from datetime import datetime, timedelta, timezone as dt_timezone
from unittest.mock import patch
from pathlib import Path
from django.test import TestCase
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from missions.models import (User, Team, TeamMember, Mission, TeamMission, MissionRequest,
    Question, DailyQuestion, DailyQuestionAnswer, Competition, PointTransaction)

class ReadContracts(TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 10, 12, tzinfo=dt_timezone.utc)
        self.clock = patch('django.utils.timezone.now', return_value=self.now)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.user = User.objects.create_user(username='reader', total_points=90)
        self.other = User.objects.create_user(username='other', total_points=120)
        self.staff = User.objects.create_user(username='staff', is_staff=True)
        self.team = Team.objects.create(name='Team')
        TeamMember.objects.create(user=self.user, team=self.team)
        self.global_mission = Mission.objects.create(title='Global', is_global=True, show_on_home=True)
        self.team_mission = Mission.objects.create(title='Team only', show_on_home=True)
        TeamMission.objects.create(team=self.team, mission=self.team_mission)
        Mission.objects.create(title='Private', show_on_home=True)
        MissionRequest.objects.create(user=self.user, mission=self.global_mission, team=self.team)
        q = Question.objects.create(text='Question', option_1='A', option_2='B', option_3='C', option_4='D', correct_option=1)
        self.daily = DailyQuestion.objects.create(question=q, publish_date=self.now.date())
        DailyQuestionAnswer.objects.create(user=self.other, daily_question=self.daily, selected_option=2)
        Competition.objects.create(title='Active', start_date=self.now-timedelta(days=1), end_date=self.now+timedelta(days=1), status='active')
        PointTransaction.objects.create(user=self.user, transaction_type='bonus', title='Reward', points=90)
        self.client.force_login(self.user)

    def test_mission_visibility_and_daily_scoping(self):
        from missions.views import get_user_available_missions, get_user_team, has_pending_request_today, has_completed_today
        self.assertEqual(get_user_team(self.user), self.team)
        self.assertIsNone(get_user_team(self.other))
        self.assertSetEqual(set(get_user_available_missions(self.user)), {self.global_mission, self.team_mission})
        self.assertEqual(list(get_user_available_missions(self.other)), [self.global_mission])
        self.assertTrue(has_pending_request_today(self.user, self.global_mission))
        self.assertFalse(has_pending_request_today(self.other, self.global_mission))
        self.assertFalse(has_completed_today(self.user, self.global_mission))
        from django.test import RequestFactory
        from missions.views import daily_questions_page
        request = RequestFactory().get('/daily/')
        request.user = self.user
        with patch('missions.views.render') as render:
            daily_questions_page(request)
        context = render.call_args.args[2]
        self.assertEqual(context['answered_ids'], [])
        self.assertEqual(list(context['daily_questions']), [self.daily])

    def test_month_helpers_preserve_calendar_contract(self):
        from missions.views import get_shamsi_month_range, get_persian_month_name, get_user_months_shamsi
        start, end, label = get_shamsi_month_range('1405-01')
        self.assertIsNone(start.tzinfo)
        self.assertLess(start, end)
        self.assertEqual(label, 'فروردین 1405')
        self.assertEqual(get_persian_month_name(0), '')
        self.assertEqual(get_persian_month_name(12), 'اسفند')
        self.assertEqual(get_user_months_shamsi(self.user)[0]['total'], 90)
        self.assertEqual(get_user_months_shamsi(self.other), [])

    def test_read_http_contract_snapshot(self):
        from django.db.models import Model, QuerySet
        def norm(value):
            if isinstance(value, Model): return [value._meta.label, value.pk]
            if isinstance(value, QuerySet): return [norm(v) for v in value]
            if isinstance(value, dict): return {str(k): norm(v) for k,v in value.items()}
            if isinstance(value, (tuple,list)): return [norm(v) for v in value]
            if isinstance(value, (str,int,float,bool)) or value is None: return value
            if hasattr(value,'isoformat'): return value.isoformat()
            return type(value).__name__
        cases = ['missions:home','missions:profile','missions:league_list','missions:daily_questions', 'missions:competition_list','missions:treasure_box', 'dashboard:home','dashboard:teams','dashboard:users','dashboard:missions','dashboard:questions','dashboard:daily_questions','dashboard:transactions']
        snapshots = {}
        self.client.raise_request_exception = False
        for actor in (None,self.user,self.staff):
            if actor: self.client.force_login(actor)
            else: self.client.logout()
            for name in cases:
                with CaptureQueriesContext(connection) as queries:
                    response = self.client.get(reverse(name))
                    # Last context layer is the view's explicit dictionary.
                    context = norm(response.context[-1].dicts[-1]) if response.context and response.status_code < 500 else None
                if response.status_code == 500:
                    self.assertIsNotNone(response.exc_info)
                    self.assertEqual(name, 'missions:daily_questions')
                    self.assertEqual(response.exc_info[0].__name__, 'NoReverseMatch')
                    self.assertIn("'leaderboard'", str(response.exc_info[1]))
                else:
                    self.assertIn(response.status_code, (200,302))
                snapshots[f'{actor.username if actor else "anonymous"}:{name}'] = {
                    'error': str(response.exc_info[1]) if response.exc_info else None,
                    'status':response.status_code,'location':response.get('Location'),
                    'templates':sorted(set(t.name for t in response.templates if t.name)),
                    'context':context,'queries':len(queries),
                }
        destination=os.environ.get('MODERNIZATION_SNAPSHOT')
        if destination: Path(destination).write_text(json.dumps(snapshots,indent=2,ensure_ascii=False),encoding='utf8')
