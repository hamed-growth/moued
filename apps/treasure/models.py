"""Persistence models for the treasure domain."""

from django.db import models
from apps.accounts.models import User


class TreasureCategory(models.Model):
    """دسته‌بندی آیتم‌های صندوق گنج"""
    name = models.CharField(
        max_length=80, verbose_name="نام دسته‌بندی",
        help_text="مثلاً: کارت هدیه، کتاب، خوراکی"
    )
    slug = models.SlugField(
        max_length=80, unique=True, verbose_name="شناسه (slug)",
        help_text="برای URL — مثلاً: gift-card، book"
    )
    icon = models.CharField(
        max_length=50, default='fa-tag', verbose_name="آیکون (Font Awesome)",
        help_text="مثلاً: fa-gift، fa-book، fa-utensils"
    )
    color = models.CharField(
        max_length=20, default='#d4a017', verbose_name="رنگ",
        help_text="کد رنگ HEX — مثلاً: #d4a017"
    )
    order = models.PositiveIntegerField(
        default=0, verbose_name="ترتیب نمایش",
        help_text="عدد کوچکتر = نمایش بالاتر"
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال است؟")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        app_label = 'missions'
        verbose_name = "دسته‌بندی صندوق گنج"
        verbose_name_plural = "دسته‌بندی‌های صندوق گنج"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class TreasureItem(models.Model):
    """آیتم قابل خرید در صندوق گنج (فروشگاه سکه‌ای)"""
    category = models.ForeignKey(
        TreasureCategory, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='items',
        verbose_name="دسته‌بندی"
    )
    name = models.CharField(max_length=150, verbose_name="نام آیتم")
    description = models.TextField(
        blank=True, null=True, verbose_name="توضیحات",
        help_text="توضیح کوتاه درباره آیتم."
    )
    image = models.ImageField(
        upload_to='treasure/items/', verbose_name="تصویر آیتم",
        help_text="تصویر آیتم را آپلود کنید."
    )
    price = models.PositiveIntegerField(
        default=100, verbose_name="قیمت (سکه)",
        help_text="سکه لازم برای خرید این آیتم."
    )
    stock = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="موجودی",
        help_text="تعداد قابل خرید. اگر خالی باشد = نامحدود."
    )
    is_featured = models.BooleanField(
        default=False, verbose_name="آیتم ویژه",
        help_text="آیتم‌های ویژه در بالای فروشگاه نمایش داده می‌شوند."
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال است؟")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        app_label = 'missions'
        verbose_name = "آیتم صندوق گنج"
        verbose_name_plural = "آیتم‌های صندوق گنج"
        ordering = ['-is_featured', '-created_at']

    def is_available(self):
        if not self.is_active:
            return False
        if self.stock is None:
            return True
        return self.stock > 0

    def __str__(self):
        return f"{self.name} ({self.price} سکه)"


class TreasurePurchase(models.Model):
    """تاریخچه خریدهای کاربر از صندوق گنج"""
    STATUS_CHOICES = (
        ('pending', 'در انتظار تأیید'),
        ('delivered', 'تأیید شده'),
        ('cancelled', 'رد شده'),
    )

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='treasure_purchases', verbose_name="کاربر"
    )
    item = models.ForeignKey(
        TreasureItem, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='purchases',
        verbose_name="آیتم"
    )
    item_name = models.CharField(
        max_length=150, verbose_name="نام آیتم (در زمان خرید)",
        help_text="نام آیتم در زمان خرید — در صورت حذف آیتم، این باقی می‌ماند."
    )
    item_price = models.PositiveIntegerField(
        verbose_name="قیمت (در زمان خرید)"
    )
    currency = models.CharField(
        max_length=6, choices=(('points', 'امتیاز'), ('coins', 'سکه')),
        default='points', verbose_name='ارز خرید',
    )
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default='pending',
        verbose_name="وضعیت"
    )
    admin_note = models.TextField(
        blank=True, null=True, verbose_name="یادداشت مدیر",
        help_text="مثلاً توضیح تحویل یا دلیل لغو."
    )
    purchased_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان خرید")
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان تحویل")

    class Meta:
        app_label = 'missions'
        verbose_name = "خرید از صندوق گنج"
        verbose_name_plural = "خریدهای صندوق گنج"
        ordering = ['-purchased_at']

    def deliver(self, admin_note=None):
        from apps.treasure.services.delivery import deliver_purchase

        return deliver_purchase(self, admin_note)

    def reject(self, admin_note=None):
        from apps.treasure.services.delivery import reject_purchase

        return reject_purchase(self, admin_note)

    def __str__(self):
        return f"{self.user.username} → {self.item_name} ({self.item_price} سکه)"
