from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from apps.competitions.models import (
    Competition,
    CompetitionAnswer,
    CompetitionQuestion,
    CompetitionRegistration,
)
from apps.competitions.services.management import (
    activate_competitions,
    finalize_competitions,
    save_competition_changes,
)


class CompetitionQuestionInline(admin.TabularInline):
    model = CompetitionQuestion
    extra = 1
    autocomplete_fields = ('question',)
    ordering = ('order',)
    fields = ('question', 'order', 'points_override')


class CompetitionAdminForm(forms.ModelForm):
    def clean_status(self):
        status = self.cleaned_data['status']
        if status == 'finished':
            raise forms.ValidationError("برای پایان مسابقه از عملیات نهایی‌سازی استفاده کنید.")
        return status


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    form = CompetitionAdminForm
    list_display = (
        'title', 'status_badge', 'start_date', 'end_date',
        'is_featured', 'points_per_correct',
        'max_questions', 'registrations_count',
    )
    list_filter = ('status', 'is_featured', 'start_date')
    search_fields = ('title', 'description')
    date_hierarchy = 'start_date'
    inlines = [CompetitionQuestionInline]

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('title', 'description', 'is_featured', 'status')
        }),
        ('دوره زمانی', {
            'fields': ('start_date', 'end_date')
        }),
        ('امتیازدهی و محدودیت‌ها', {
            'fields': ('points_per_correct', 'max_questions', 'time_limit_minutes')
        }),
        ('جوایز', {
            'fields': (
                'first_prize_points', 'second_prize_points',
                'third_prize_points', 'participation_bonus',
            )
        }),
    )

    actions = ['finalize_competition', 'activate_competitions']

    def get_readonly_fields(self, request, obj=None):
        if obj is not None and obj.status == 'finished':
            return (*super().get_readonly_fields(request, obj), 'status')
        return super().get_readonly_fields(request, obj)

    def save_model(self, request, obj, form, change):
        if not change:
            return super().save_model(request, obj, form, change)
        save_competition_changes(obj, form.changed_data)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['add_question_url'] = reverse('admin:missions_question_add')
        return super().change_view(request, object_id, form_url, extra_context)

    @admin.display(description="وضعیت")
    def status_badge(self, obj):
        colors = {
            'draft': 'gray', 'upcoming': 'orange', 'active': 'green',
            'finished': 'blue', 'cancelled': 'red',
        }
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display(),
        )

    @admin.display(description="شرکت‌کنندگان")
    def registrations_count(self, obj):
        return obj.registrations.count()

    @admin.action(description="پایان مسابقه و اهدای جوایز")
    def finalize_competition(self, request, queryset):
        count = finalize_competitions(queryset)
        self.message_user(request, f"{count} مسابقه پایان یافت و جوایز اهدا شد.")

    @admin.action(description="فعال‌سازی مسابقات انتخاب‌شده")
    def activate_competitions(self, request, queryset):
        count = activate_competitions(queryset)
        self.message_user(request, f"{count} مسابقه فعال شد.")


@admin.register(CompetitionQuestion)
class CompetitionQuestionAdmin(admin.ModelAdmin):
    list_display = (
        'competition', 'question_short', 'order',
        'points_override', 'effective_points',
    )
    list_filter = ('competition',)
    search_fields = ('competition__title', 'question__text')
    autocomplete_fields = ('question',)
    ordering = ('competition', 'order')

    @admin.display(description="سوال")
    def question_short(self, obj):
        return obj.question.text[:50]

    @admin.display(description="امتیاز مؤثر")
    def effective_points(self, obj):
        return obj.get_points()


@admin.register(CompetitionRegistration)
class CompetitionRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'competition', 'total_correct', 'total_wrong',
        'total_answered', 'score', 'rank', 'is_completed',
    )
    list_filter = ('is_completed', 'competition')
    search_fields = ('user__username', 'competition__title')
    readonly_fields = ('registered_at', 'started_at', 'finished_at', 'is_completed')
    date_hierarchy = 'registered_at'
    autocomplete_fields = ('user', 'competition')

    def save_model(self, request, obj, form, change):
        if change:
            obj.save(update_fields=form.changed_data)
        else:
            super().save_model(request, obj, form, change)


@admin.register(CompetitionAnswer)
class CompetitionAnswerAdmin(admin.ModelAdmin):
    list_display = (
        'registration', 'question_short', 'selected_option',
        'is_correct_badge', 'points_awarded', 'answered_at',
    )
    list_filter = ('is_correct', 'answered_at', 'registration__competition')
    search_fields = ('registration__user__username', 'question__text')
    readonly_fields = ('answered_at',)
    date_hierarchy = 'answered_at'
    autocomplete_fields = ('question',)

    @admin.display(description="سوال")
    def question_short(self, obj):
        return obj.question.text[:50]

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
