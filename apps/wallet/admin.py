from django.contrib import admin
from apps.wallet.models import PointTransaction


@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'transaction_type', 'title',
        'points', 'coins', 'created_at',
    )
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('user__username', 'title')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
