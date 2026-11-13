from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from unittest.mock import patch

from django.db import DatabaseError, connection, connections, transaction
from django.db.models import QuerySet
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.treasure.models import TreasureItem, TreasurePurchase
from apps.wallet.models import PointTransaction


class PurchaseFixtures:
    def buyer(self, username="buyer", points=20):
        return User.objects.create_user(username=username, total_points=7, total_coins=points)

    def item(self, stock=1, name="Fixture"):
        return TreasureItem.objects.create(name=name, price=10, stock=stock)

    def buy(self, client, item):
        return client.post(reverse("missions:buy_treasure_item", args=[item.pk]))

    def assert_accounting(self, user, item, *, points, stock, count):
        user.refresh_from_db()
        item.refresh_from_db()
        self.assertEqual((user.total_points, user.total_coins, item.stock), (7, points, stock))
        purchases = TreasurePurchase.objects.filter(user=user, item=item)
        self.assertEqual(list(purchases.values_list("status", "item_price", "item_name")),
                         [("pending", 10, item.name)] * count)
        entries = PointTransaction.objects.filter(user=user, transaction_type="treasure")
        self.assertEqual(list(entries.values_list("points", "coins")), [(0, -10)] * count)


class PurchaseTransactionTests(PurchaseFixtures, TestCase):
    def setUp(self):
        self.user = self.buyer()
        self.item_for_sale = self.item()
        self.client.force_login(self.user)

    def test_exact_balance_and_last_unit(self):
        self.user.total_coins = 10
        self.user.save(update_fields=["total_coins"])
        response = self.buy(self.client, self.item_for_sale)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["new_total"], 0)
        self.assertEqual(response.json()["purchase_id"], TreasurePurchase.objects.get().pk)
        self.assert_accounting(self.user, self.item_for_sale, points=0, stock=0, count=1)

    def test_insufficient_points(self):
        self.user.total_coins = 9
        self.user.save(update_fields=["total_coins"])
        self.assertEqual(self.buy(self.client, self.item_for_sale).status_code, 400)
        self.assert_accounting(self.user, self.item_for_sale, points=9, stock=1, count=0)

    def test_insufficient_stock(self):
        item = self.item(stock=0)
        self.assertEqual(self.buy(self.client, item).status_code, 400)
        self.assert_accounting(self.user, item, points=20, stock=0, count=0)

    def test_independent_repeated_purchases_with_unlimited_stock(self):
        item = self.item(stock=None)
        ids = []
        for balance in (10, 0):
            response = self.buy(self.client, item)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["new_total"], balance)
            ids.append(response.json()["purchase_id"])
        self.assertNotEqual(*ids)
        self.assert_accounting(self.user, item, points=0, stock=None, count=2)

    def test_reservation_conflict_rolls_back_debit(self):
        update = QuerySet.update

        def reserve_conflict(queryset, **fields):
            if queryset.model is TreasureItem:
                self.assertEqual(User.objects.get(pk=self.user.pk).total_coins, 10)
                return 0
            return update(queryset, **fields)

        with patch.object(QuerySet, "update", reserve_conflict):
            response = self.buy(self.client, self.item_for_sale)
        self.assertEqual(response.status_code, 400)
        self.assert_accounting(self.user, self.item_for_sale, points=20, stock=1, count=0)

    def assert_database_failure(self, response):
        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.json()["success"])
        self.assertNotIn("synthetic database error", response.content.decode())
        self.assert_accounting(self.user, self.item_for_sale, points=20, stock=1, count=0)

    def test_balance_or_inventory_write_exception_rolls_back(self):
        update = QuerySet.update
        for model in (User, TreasureItem):
            with self.subTest(model=model):
                def fail_update(queryset, **fields):
                    result = update(queryset, **fields)
                    if queryset.model is model:
                        raise DatabaseError("synthetic database error")
                    return result

                with patch.object(QuerySet, "update", fail_update), self.assertLogs("apps.treasure.views", "ERROR"):
                    response = self.buy(self.client, self.item_for_sale)
                self.assert_database_failure(response)

    def test_ledger_or_purchase_creation_exception_rolls_back(self):
        for manager in (PointTransaction.objects, TreasurePurchase.objects):
            with self.subTest(model=manager.model):
                create = manager.create

                def fail_create(**fields):
                    create(**fields)
                    raise DatabaseError("synthetic database error")

                with patch.object(manager, "create", side_effect=fail_create), self.assertLogs("apps.treasure.views", "ERROR"):
                    response = self.buy(self.client, self.item_for_sale)
                self.assert_database_failure(response)


class PurchaseConcurrencyTests(PurchaseFixtures, TransactionTestCase):
    def setUp(self):
        database = str(connection.settings_dict["NAME"])
        self.assertEqual(connection.vendor, "sqlite")
        self.assertTrue(Path(database).is_file(), "Use disposable file-backed SQLite test settings.")

    def client_for(self, user):
        client = Client()
        client.force_login(user)
        return client

    def worker_purchase(self, client, item):
        try:
            return self.buy(client, item)
        finally:
            connections.close_all()

    def race(self, orders):
        clients = [(self.client_for(user), item) for user, item in orders]
        ready = Barrier(2, timeout=10)
        available = TreasureItem.is_available

        def synchronized_availability(item):
            result = available(item)
            ready.wait()
            return result

        with patch.object(TreasureItem, "is_available", synchronized_availability):
            with ThreadPoolExecutor(max_workers=2) as workers:
                jobs = [workers.submit(self.worker_purchase, client, item) for client, item in clients]
                return [job.result(timeout=20) for job in jobs]

    def test_two_buyers_compete_for_last_unit(self):
        buyers = [self.buyer("first"), self.buyer("second")]
        item = self.item()
        responses = self.race([(user, item) for user in buyers])
        self.assertCountEqual([r.status_code for r in responses], [200, 400])
        for user, response in zip(buyers, responses, strict=True):
            bought = int(response.status_code == 200)
            self.assert_accounting(user, item, points=20 - 10 * bought, stock=0, count=bought)

    def test_two_items_compete_for_same_buyers_last_points(self):
        user = self.buyer(points=10)
        items = [self.item(name="First"), self.item(name="Second")]
        responses = self.race([(user, item) for item in items])
        self.assertCountEqual([r.status_code for r in responses], [200, 400])
        user.refresh_from_db()
        self.assertEqual((user.total_points, user.total_coins), (7, 0))
        self.assertEqual(list(PointTransaction.objects.values_list("points", "coins")), [(0, -10)])
        for item, response in zip(items, responses, strict=True):
            bought = int(response.status_code == 200)
            item.refresh_from_db()
            self.assertEqual(item.stock, 1 - bought)
            self.assertEqual(TreasurePurchase.objects.filter(user=user, item=item, status="pending").count(), bought)
        self.assertEqual(TreasurePurchase.objects.count(), 1)

    def test_two_different_items_both_commit_when_funded(self):
        user = self.buyer()
        items = [self.item(name="First"), self.item(name="Second")]
        responses = self.race([(user, item) for item in items])
        self.assertEqual([r.status_code for r in responses], [200, 200])
        self.assertCountEqual([r.json()["new_total"] for r in responses], [10, 0])
        user.refresh_from_db()
        self.assertEqual((user.total_points, user.total_coins), (7, 0))
        self.assertEqual(list(PointTransaction.objects.values_list("points", "coins")), [(0, -10)] * 2)
        self.assertCountEqual(TreasurePurchase.objects.values_list("item_id", "status", "item_price"),
                              [(item.pk, "pending", 10) for item in items])
        for item in items:
            item.refresh_from_db()
            self.assertEqual(item.stock, 0)

    def test_real_sqlite_lock_returns_failure_without_accounting_changes(self):
        user = self.buyer()
        item = self.item()
        client = self.client_for(user)

        def attempt_without_waiting():
            # Apply a zero wait only to this disposable worker connection.
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA busy_timeout = 0")
            return self.worker_purchase(client, item)

        with ThreadPoolExecutor(max_workers=1) as workers:
            with transaction.atomic():
                User.objects.filter(pk=user.pk).update(total_coins=20)
                with self.assertLogs("apps.treasure.views", "ERROR") as logs:
                    response = workers.submit(attempt_without_waiting).result(timeout=10)
        self.assertIn("database is locked", "\n".join(logs.output))
        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.json()["success"])
        self.assertNotIn("locked", response.content.decode())
        self.assert_accounting(user, item, points=20, stock=1, count=0)
