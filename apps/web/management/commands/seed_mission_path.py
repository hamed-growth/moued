from datetime import time
from django.core.management.base import BaseCommand
from apps.missions.models import Mission, MissionCategory


class Command(BaseCommand):
    help = 'Create six sample global missions for the path preview.'

    def handle(self, *args, **options):
        category, _ = MissionCategory.objects.get_or_create(slug='daily-path', defaults={'name': 'کارهای روزانه'})
        samples = [
            ('نماز صبح', 15, time(3), time(6)),
            ('کمک به خانواده', 10, None, None),
            ('خواندن چند صفحه کتاب', 12, None, None),
            ('مرتب کردن وسایل', 8, None, None),
            ('گفت‌وگوی خوب', 10, None, None),
            ('مرور دانسته‌ها', 14, None, None),
        ]
        for order, (title, points, start, end) in enumerate(samples):
            Mission.objects.get_or_create(title=title, defaults={
                'category': category, 'points': points, 'is_global': True, 'is_active': True,
                'has_time_limit': bool(start), 'start_time': start, 'end_time': end, 'home_order': order,
            })
        self.stdout.write(self.style.SUCCESS('شش مأموریت نمونه آماده شد.'))
