from django.contrib import admin
from django.utils.html import format_html
from apps.treasure.models import TreasureCategory, TreasureItem, TreasurePurchase


@admin.register(TreasureCategory)
class TreasureCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon_preview', 'order', 'is_active', 'items_count')
    list_filter = ('is_active',)
    list_editable = ('order', 'is_active')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')

    fieldsets = (
        ('اطلاعات دسته‌بندی', {
            'fields': ('name', 'slug')
        }),
        ('ظاهر', {
            'fields': ('icon', 'color', 'order')
        }),
        ('وضعیت', {
            'fields': ('is_active',)
        }),
    )

    @admin.display(description="آیکون")
    def icon_preview(self, obj):
        return format_html(
            '<i class="fa-solid {}" style="color:{};font-size:1.3rem;"></i> '
            '<code style="font-size:0.8rem;">{}</code>',
            obj.icon, obj.color, obj.icon,
        )

    @admin.display(description="تعداد آیتم")
    def items_count(self, obj):
        return obj.items.count()


@admin.register(TreasureItem)
class TreasureItemAdmin(admin.ModelAdmin):
    list_display = (
        'image_preview', 'name', 'category', 'price',
        'stock_display', 'is_featured', 'is_active', 'created_at',
    )
    list_filter = ('category', 'is_featured', 'is_active')
    list_editable = ('is_featured', 'is_active', 'price')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'image_preview_large')
    autocomplete_fields = ('category',)

    fieldsets = (
        ('اطلاعات آیتم', {
            'fields': ('name', 'description', 'category')
        }),
        ('تصویر', {
            'fields': ('image', 'image_preview_large')
        }),
        ('قیمت و موجودی', {
            'fields': ('price', 'stock', 'is_featured', 'is_active')
        }),
        ('زمان', {
            'fields': ('created_at',)
        }),
    )

    @admin.display(description="تصویر")
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:50px;height:50px;'
                'object-fit:cover;border-radius:8px;" />',
                obj.image.url
            )
        return "—"

    @admin.display(description="پیش‌نمایش تصویر")
    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:300px;border-radius:12px;" />',
                obj.image.url
            )
        return "—"

    @admin.display(description="موجودی")
    def stock_display(self, obj):
        if obj.stock is None:
            return format_html('<span style="color:green;">نامحدود</span>')
        if obj.stock == 0:
            return format_html('<span style="color:red;font-weight:bold;">ناموجود</span>')
        if obj.stock <= 3:
            return format_html(
                '<span style="color:orange;font-weight:bold;">{} (کم)</span>',
                obj.stock
            )
        return obj.stock


@admin.register(TreasurePurchase)
class TreasurePurchaseAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'item_name', 'item_price',
        'status_badge', 'purchased_at', 'delivered_at',
    )
    list_filter = ('status', 'purchased_at')
    search_fields = ('user__username', 'item_name')
    readonly_fields = ('user', 'item', 'item_name', 'item_price', 'currency', 'purchased_at', 'delivered_at', 'status')
    date_hierarchy = 'purchased_at'

    fieldsets = (
        ('اطلاعات خرید', {
            'fields': ('user', 'item', 'item_name', 'item_price', 'currency', 'purchased_at')
        }),
        ('وضعیت', {
            'fields': ('status', 'admin_note', 'delivered_at')
        }),
    )

    actions = ['mark_delivered', 'mark_rejected']

    @admin.display(description="وضعیت")
    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'delivered': '#10b981',
            'cancelled': '#ef4444',
        }
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            colors.get(obj.status, '#000'),
            obj.get_status_display(),
        )

    @admin.action(description="علامت‌گذاری به‌عنوان تحویل شده")
    def mark_delivered(self, request, queryset):
        count = 0
        for p in queryset.filter(status='pending'):
            if p.deliver():
                count += 1
        self.message_user(request, f"{count} خرید به‌عنوان تحویل شده علامت‌گذاری شد.")

    @admin.action(description="رد درخواست و بازگرداندن سکه و موجودی")
    def mark_rejected(self, request, queryset):
        count = 0
        for purchase in queryset.filter(status='pending'):
            if purchase.reject():
                count += 1
        self.message_user(request, f"{count} درخواست رد و بازپرداخت شد.")
