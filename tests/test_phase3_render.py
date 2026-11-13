from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.competitions.models import Competition
from apps.competitions.models import CompetitionRegistration, CompetitionQuestion
from apps.missions.models import Mission
from apps.questions.models import DailyQuestion, DailyQuestionAnswer, Question
from apps.treasure.models import TreasureItem, TreasurePurchase


class Phase3RenderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='phase3-reader', password='test-pass')
        self.client.force_login(self.user)

    def make_daily(self):
        question = Question.objects.create(
            text='پرسش نمونه', option_1='یک', option_2='دو',
            option_3='سه', option_4='چهار', correct_option=2,
        )
        return DailyQuestion.objects.create(question=question, publish_date=timezone.localdate())

    def test_daily_with_question_renders_without_exposing_answer(self):
        self.make_daily()
        response = self.client.get(reverse('missions:daily_questions'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'پرسش نمونه')
        self.assertContains(response, reverse('missions:league_list'))
        self.assertNotContains(response, 'data-correct-option')

    def test_daily_already_answered_renders(self):
        daily = self.make_daily()
        DailyQuestionAnswer.objects.create(user=self.user, daily_question=daily, selected_option=1)
        response = self.client.get(reverse('missions:daily_questions'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(daily.id, response.context['answered_ids'])

    def test_daily_empty_renders(self):
        response = self.client.get(reverse('missions:daily_questions'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'امروز سوالی منتشر نشده')

    def test_archive_empty_renders(self):
        response = self.client.get(reverse('missions:archive'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'هنوز مأموریتی در آرشیو نیست')
        self.assertContains(response, 'هنوز مسابقه‌ای در آرشیو نیست')

    def test_archive_with_data_renders(self):
        Mission.objects.create(title='مأموریت قدیمی', is_active=False)
        now = timezone.now()
        Competition.objects.create(title='مسابقه قدیمی', start_date=now-timedelta(days=2), end_date=now-timedelta(days=1), status='finished')
        response = self.client.get(reverse('missions:archive'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'مأموریت قدیمی')
        self.assertContains(response, 'مسابقه قدیمی')

    def test_user_page_smoke_empty_and_representative(self):
        now = timezone.now()
        competition = Competition.objects.create(title='نمونه', start_date=now-timedelta(hours=1), end_date=now+timedelta(hours=1), status='active')
        question = Question.objects.create(text='سؤال مسابقه', option_1='یک', option_2='دو', option_3='سه', option_4='چهار', correct_option=1)
        CompetitionQuestion.objects.create(competition=competition, question=question)
        CompetitionRegistration.objects.create(competition=competition, user=self.user)
        self.make_daily()
        for name, args in [
            ('home', []), ('profile', []), ('daily_questions', []),
            ('competition_list', []), ('competition_detail', [competition.id]),
            ('competition_play', [competition.id]), ('treasure_box', []),
            ('league_list', []), ('archive', []),
        ]:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse('missions:' + name, args=args)).status_code, 200)

    def test_anonymous_base_and_auth_pages(self):
        self.client.logout()
        for name in ('home', 'login', 'register'):
            with self.subTest(page=name):
                response = self.client.get(reverse('missions:' + name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'href="#main-content"')

    def test_staff_page_smoke(self):
        self.user.is_staff = True
        self.user.save(update_fields=['is_staff'])
        for name in ('users', 'teams', 'missions', 'mission_requests', 'competitions', 'questions', 'daily_questions', 'transactions'):
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse('dashboard:' + name)).status_code, 200)
        for name in ('home', 'treasure'):
            self.assertEqual(self.client.get(reverse('dashboard:' + name)).status_code, 200)
        item = TreasureItem.objects.create(name='جایزه نمونه', price=10)
        TreasurePurchase.objects.create(user=self.user, item=item, item_name=item.name, item_price=10)
        for name in ('home', 'treasure'):
            with self.subTest(page_with_pending_purchase=name):
                self.assertEqual(self.client.get(reverse('dashboard:' + name)).status_code, 200)
