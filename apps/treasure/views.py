import logging
from apps.treasure.selectors.storefront import get_storefront_context
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import DatabaseError
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_POST
from apps.treasure.services.checkout import InsufficientCoins, OutOfStock, purchase_treasure_item
from apps.treasure.models import TreasureItem

logger = logging.getLogger(__name__)


@login_required
def treasure_box(request):
    context = get_storefront_context(request.user, request.GET.get('category', ''))
    return render(request, 'missions/treasure_box.html', context)


@login_required
@require_POST
def buy_treasure_item(request, item_id):
    """خرید آیتم از فروشگاه صندوق گنج"""
    try:
        purchase, new_total = purchase_treasure_item(request.user, item_id)
    except TreasureItem.DoesNotExist as exc:
        raise Http404('No TreasureItem matches the given query.') from exc
    except OutOfStock:
        return JsonResponse({
            'success': False,
            'message': 'این آیتم موجود نیست.'
        }, status=400)
    except InsufficientCoins as exc:
        return JsonResponse({
            'success': False,
            'message': f'سکه کافی ندارید. {exc.shortfall} سکه دیگر لازم دارید.'
        }, status=400)
    except DatabaseError:
        logger.exception("Treasure purchase database operation failed")
        return JsonResponse({
            'success': False,
            'message': 'خرید انجام نشد. لطفاً دوباره تلاش کنید.'
        }, status=503)

    return JsonResponse({
        'success': True,
        'message': f'درخواست خرید «{purchase.item_name}» ثبت شد و در انتظار تأیید مدیر است.',
        'new_total': new_total,
        'purchase_id': purchase.id,
    })
