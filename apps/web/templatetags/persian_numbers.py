from django import template

register = template.Library()
DIGITS = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')


@register.filter
def fa_digits(value):
    """Display ASCII digits as Persian digits without changing stored values."""
    return str(value).translate(DIGITS)
