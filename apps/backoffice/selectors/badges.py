from missions.models import MissionRequest, TreasurePurchase


def get_staff_badges():
    return {
        'dash_pending_requests': MissionRequest.objects.filter(status='pending').count(),
        'dash_pending_purchases': TreasurePurchase.objects.filter(status='pending').count(),
    }