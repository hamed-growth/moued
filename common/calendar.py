"""Existing Jalali calendar conventions, including naive month boundaries."""
from datetime import datetime, time
import jdatetime

PERSIAN_MONTHS = [
    'فروردین', 'اردیبهشت', 'خرداد',
    'تیر', 'مرداد', 'شهریور',
    'مهر', 'آبان', 'آذر',
    'دی', 'بهمن', 'اسفند'
]


def get_persian_month_name(month_num):
    if 1 <= month_num <= 12:
        return PERSIAN_MONTHS[month_num - 1]
    return ''


def get_shamsi_month_range(year_month_str):
    year, month = map(int, year_month_str.split('-'))

    start_jdate = jdatetime.date(year, month, 1)
    if month == 12:
        end_jdate = jdatetime.date(year + 1, 1, 1)
    else:
        end_jdate = jdatetime.date(year, month + 1, 1)

    start_gregorian = start_jdate.togregorian()
    end_gregorian = end_jdate.togregorian()

    start_dt = datetime.combine(start_gregorian, time.min)
    end_dt = datetime.combine(end_gregorian, time.min)

    label = f"{get_persian_month_name(start_jdate.month)} {year}"

    return start_dt, end_dt, label

