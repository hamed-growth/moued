from unittest.mock import patch

from django.db import DatabaseError
from django.test import TestCase

from apps.treasure.models import TreasureItem, TreasurePurchase
from apps.treasure.services.checkout import InsufficientCoins, OutOfStock, purchase_treasure_item
from .test_treasure_transactions import PurchaseFixtures


class TreasureServiceTests(PurchaseFixtures, TestCase):
    def test_success_returns_pending_purchase_and_exact_balance(self):
        buyer = self.buyer(points=10)
        item = self.item()
        purchase, balance = purchase_treasure_item(buyer, item.pk)
        self.assertEqual(balance, 0)
        self.assertEqual(purchase, TreasurePurchase.objects.get(user=buyer, item=item))
        self.assert_accounting(buyer, item, points=0, stock=0, count=1)

    def test_unlimited_stock_accepts_independent_purchases(self):
        buyer = self.buyer()
        item = self.item(stock=None)
        first, first_balance = purchase_treasure_item(buyer, item.pk)
        second, second_balance = purchase_treasure_item(buyer, item.pk)
        self.assertNotEqual(first.pk, second.pk)
        self.assertEqual((first_balance, second_balance), (10, 0))
        self.assert_accounting(buyer, item, points=0, stock=None, count=2)

    def test_domain_failures_are_distinct_and_do_not_write(self):
        buyer = self.buyer(points=9)
        available = self.item()
        sold_out = self.item(stock=0)
        with self.assertRaises(TreasureItem.DoesNotExist):
            purchase_treasure_item(buyer, 999999)
        with self.assertRaises(OutOfStock):
            purchase_treasure_item(buyer, sold_out.pk)
        with self.assertRaises(InsufficientCoins) as error:
            purchase_treasure_item(buyer, available.pk)
        self.assertEqual(error.exception.shortfall, 1)
        self.assert_accounting(buyer, available, points=9, stock=1, count=0)
        self.assert_accounting(buyer, sold_out, points=9, stock=0, count=0)

    def test_database_error_surfaces_after_atomic_rollback(self):
        buyer = self.buyer()
        item = self.item()
        with patch.object(TreasurePurchase.objects, "create", side_effect=DatabaseError("fixture")):
            with self.assertRaises(DatabaseError):
                purchase_treasure_item(buyer, item.pk)
        self.assert_accounting(buyer, item, points=20, stock=1, count=0)
