from django.utils import timezone


def deliver_purchase(purchase, admin_note=None):
    if purchase.status == 'delivered':
        return False
    purchase.status = 'delivered'
    purchase.delivered_at = timezone.now()
    if admin_note:
        purchase.admin_note = admin_note
    purchase.save()
    return True
