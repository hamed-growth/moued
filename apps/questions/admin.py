from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from apps.questions.models import DailyQuestion, DailyQuestionAnswer, Question


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text_preview', 'correct_option')
    list_filter = ('correct_option',)
    search_fields = ('text',)
    ordering = ('-id',)

    @admin.display(description="متن سوال")
    def text_preview(self, obj):
        return obj.text[:60]


@admin.register(DailyQuestion)
class DailyQuestionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'short_question', 'publish_date',
        'points', 'difficulty', 'is_active', 'answered_count',
    )
    list_filter = ('is_active', 'difficulty', 'publish_date')
    search_fields = ('question__text',)
    date_hierarchy = 'publish_date'
    list_editable = ('is_active',)
    autocomplete_fields = ('question',)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['add_question_url'] = reverse('admin:missions_question_add')
        return super().change_view(request, object_id, form_url, extra_context)

    @admin.display(description="سوال")
    def short_question(self, obj):
        return obj.question.text[:50]

    @admin.display(description="تعداد پاسخ‌ها")
    def answered_count(self, obj):
        return obj.answers.count()


@admin.register(DailyQuestionAnswer)
class DailyQuestionAnswerAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'daily_question', 'is_correct_badge',
        'selected_option', 'points_awarded', 'answered_at',
    )
    list_filter = ('is_correct', 'answered_at')
    search_fields = ('user__username', 'daily_question__question__text')
    date_hierarchy = 'answered_at'
    readonly_fields = ('answered_at',)

    @admin.display(description="وضعیت")
    def is_correct_badge(self, obj):
        if obj.is_correct:
            return format_html(
                '<span style="color:{};font-weight:bold;">{}</span>',
                'green', '✓ صحیح',
            )
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            'red', '✗ غلط',
        )
