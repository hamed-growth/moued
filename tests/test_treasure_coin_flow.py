from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.treasure.models import TreasureItem, TreasurePurchase
from apps.wallet.models import PointTransaction


class TreasureCoinFlowTests(TestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(username='buyer_coin', total_points=50, total_coins=20)
        self.staff = User.objects.create_user(username='staff_coin', is_staff=True)
        self.item = TreasureItem.objects.create(name='Gift', price=10, stock=1)

    def test_purchase_approval_keeps_points_and_reserved_stock(self):
        self.client.force_login(self.buyer)
        response = self.client.post(reverse('missions:buy_treasure_item', args=[self.item.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['new_total'], 10)
        purchase = TreasurePurchase.objects.get(pk=response.json()['purchase_id'])
        self.assertEqual((purchase.status, purchase.currency), ('pending', 'coins'))
        self.client.force_login(self.staff)
        url = reverse('dashboard:treasure_purchase_deliver', args=[purchase.pk])
        self.client.post(url)
        self.client.post(url)
        self.buyer.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual((self.buyer.total_points, self.buyer.total_coins, self.item.stock), (50, 10, 0))
        self.assertEqual(list(PointTransaction.objects.filter(user=self.buyer).values_list('points', 'coins')), [(0, -10)])

    def test_rejection_refunds_exactly_once(self):
        self.client.force_login(self.buyer)
        purchase_id = self.client.post(reverse('missions:buy_treasure_item', args=[self.item.pk])).json()['purchase_id']
        self.client.force_login(self.staff)
        url = reverse('dashboard:treasure_purchase_reject', args=[purchase_id])
        self.client.post(url)
        self.client.post(url)
        self.buyer.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual((self.buyer.total_points, self.buyer.total_coins, self.item.stock), (50, 20, 1))
        self.assertEqual(TreasurePurchase.objects.get(pk=purchase_id).status, 'cancelled')
        self.assertCountEqual(PointTransaction.objects.filter(user=self.buyer).values_list('points', 'coins'), [(0, -10), (0, 10)])

    def test_reject_message_names_coin_currency(self):
        purchase = TreasurePurchase.objects.create(user=self.buyer, item=self.item, item_name='Gift', item_price=10, currency='coins')
        self.client.force_login(self.staff)
        response = self.client.post(reverse('dashboard:treasure_purchase_reject', args=[purchase.pk]), follow=True)
        self.assertContains(response, 'سکه و موجودی برگشت')

    def test_reject_message_names_point_currency(self):
        purchase = TreasurePurchase.objects.create(user=self.buyer, item=self.item, item_name='Gift', item_price=10, currency='points')
        self.client.force_login(self.staff)
        response = self.client.post(reverse('dashboard:treasure_purchase_reject', args=[purchase.pk]), follow=True)
        self.assertContains(response, 'امتیاز و موجودی برگشت')

    def test_legacy_pending_purchase_refunds_points(self):
        purchase = TreasurePurchase.objects.create(user=self.buyer, item=self.item, item_name='Gift', item_price=10)
        self.assertTrue(purchase.reject())
        self.buyer.refresh_from_db()
        self.assertEqual((self.buyer.total_points, self.buyer.total_coins), (60, 20))

    def test_insufficient_coins_does_not_spend_points(self):
        self.buyer.total_coins = 9
        self.buyer.save(update_fields=['total_coins'])
        self.client.force_login(self.buyer)
        response = self.client.post(reverse('missions:buy_treasure_item', args=[self.item.pk]))
        self.assertEqual(response.status_code, 400)
        self.buyer.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual((self.buyer.total_points, self.buyer.total_coins, self.item.stock), (50, 9, 1))
        self.assertFalse(TreasurePurchase.objects.exists())

    def test_storefront_displays_coin_balance_and_price(self):
        self.client.force_login(self.buyer)
        response = self.client.get(reverse('missions:treasure_box'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<bdi data-game-digits>20</bdi> سکه', html=True)
        self.assertContains(response, '10 سکه')
        self.assertContains(response, 'سکه قابل استفاده')
        self.assertNotContains(response, 'امتیاز کافی نیست')
