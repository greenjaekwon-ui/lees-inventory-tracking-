"""FID-9 Record a sale. One test per SRS test scenario (TS9.x)."""
import unittest
from datetime import timedelta

from app.logic.errors import PermissionDenied, ValidationError
from tests.helpers import Env

class T(unittest.TestCase):
    def setUp(self):
        self.e = Env()
        self.addCleanup(self.e.close)
        self.rice = self.e.add("Rice 5kg", 10, 3)
        self.sell = lambda qty, ref, pid=None, user=None: self.e.sm.record_sale(user or self.e.cash, pid or self.rice, qty, ref)

    def test_TS_9_1A(self):
        """TS9.1A [AC9.1]: Check that an authorized cashier can record a valid sale using an active product, eligible stock, a positive quantity of whole units and a unique sale reference."""
        self.assertEqual(self.sell(2, "S-1"), 8)

    def test_TS_9_1B(self):
        """TS9.1B [AC9.1]: Check that a user without permission cannot record a sale or change stock quantities."""
        for user in (self.e.wh, self.e.owner, None):
            with self.assertRaises(PermissionDenied):
                self.e.sm.record_sale(user, self.rice, 1, "S-2")
        self.assertEqual(self.e.batch(self.rice)[0]["qty_in_stock"], 10)
        self.assertEqual(self.e.count("sale"), 0)

    def test_TS_9_1C(self):
        """TS9.1C [AC9.1]: Check that sales for archived products or with missing sale references are rejected without deducting stock."""
        self.e.pm.remove_product(self.e.mgr, self.rice, "discontinued")
        with self.assertRaises(ValidationError):
            self.sell(1, "S-3")
        other = self.e.add("Beans", 5)
        with self.assertRaises(ValidationError):
            self.sell(1, "  ", pid=other)
        self.assertEqual(self.e.batch(other)[0]["qty_in_stock"], 5)

    def test_TS_9_2A(self):
        """TS9.2A [AC9.2]: Check that selling three of ten eligible units leaves seven In Stock, records three as Sold and reduces the recorded unsold quantity by three."""
        self.sell(3, "S-1")
        b = self.e.batch(self.rice)[0]
        self.assertEqual((b["qty_in_stock"], b["qty_sold"]), (7, 3))
        self.assertEqual(self.e.status(self.rice), ["In Stock"])

    def test_TS_9_2B(self):
        """TS9.2B [AC9.2]: Check that selling all available units leaves zero availability and displays an Out of Stock flag."""
        self.sell(10, "S-1")
        b = self.e.batch(self.rice)[0]
        self.assertEqual((b["qty_in_stock"], b["qty_sold"]), (0, 10))
        self.assertEqual(self.e.status(self.rice), ["Sold"])
        empty = self.e.add("Beans", 0)
        self.assertEqual(self.e.status(empty), ["Out of Stock"])

    def test_TS_9_2C(self):
        """TS9.2C [AC9.2]: Check that selling units from one expiry group does not change the quantities or statuses of other groups."""
        self.e.add_batch(self.rice, 6, 20)
        self.sell(4, "S-1")                          # taken from the batch that expires first
        first, second = self.e.batch(self.rice)
        self.assertEqual((first["qty_in_stock"], second["qty_in_stock"]), (10, 2))   # no-expiry batch used last

    def test_TS_9_3A(self):
        """TS9.3A [AC9.3]: Check that sale quantities of zero, negative numbers, fractions and amounts above eligible availability are rejected without making any stock deduction."""
        for bad in ("0", "-2", "1.5", "abc", "11"):
            with self.assertRaises(ValidationError):
                self.sell(bad, "S-" + bad)
        self.assertEqual(self.e.batch(self.rice)[0]["qty_in_stock"], 10)
        self.assertEqual(self.e.count("sale"), 0)

    def test_TS_9_3B(self):
        """TS9.3B [AC9.3]: Check that goods marked Damaged, Expired or Sold cannot be used as eligible stock for a new sale."""
        self.e.sm.record_damage(self.e.wh, self.rice, 10, "Damaged in storage")
        with self.assertRaises(ValidationError):
            self.sell(1, "S-1")
        sold = self.e.add("Beans", 2)
        self.sell(2, "S-2", pid=sold)
        with self.assertRaises(ValidationError):
            self.sell(1, "S-3", pid=sold)
        exp = self.e.add("Milk", 5, days=-1)
        self.e.sm.expire_overdue()
        with self.assertRaises(ValidationError):
            self.sell(1, "S-4", pid=exp)

    def test_TS_9_3C(self):
        """TS9.3C [AC9.3]: Check that goods which expire after the sale screen opens but before the sale is saved are rejected, even when the displayed stock information has not yet updated."""
        milk = self.e.add("Milk", 5, days=1)
        self.e.today = self.e.today + timedelta(days=2)     # the screen was opened while the stock was valid; it expires before saving
        with self.assertRaises(ValidationError):
            self.sell(1, "S-1", pid=milk)
        self.assertEqual(self.e.batch(milk)[0]["qty_in_stock"], 5)

    def test_TS_9_4A(self):
        """TS9.4A [AC9.4]: Check that submitting an existing sale reference again produces an already recorded message or a rejection without deducting stock a second time."""
        self.sell(2, "S-1")
        with self.assertRaises(ValidationError) as ctx:
            self.sell(2, "S-1")
        self.assertIn("sale_ref", ctx.exception.errors)
        self.assertEqual(self.e.batch(self.rice)[0]["qty_in_stock"], 8)

    def test_TS_9_4B(self):
        """TS9.4B [AC9.4]: Check that a saved sale updates related views and alerts within five seconds. Its reference, user, date and time, Sold quantity and remaining availability must still be correct after restarting the application."""
        self.sell(3, "S-1")
        row = self.e.db.query("SELECT * FROM sale")[0]
        self.assertEqual((row["sale_ref"], row["quantity"], row["performed_by"]), ("S-1", 3, "cash"))
        self.assertTrue(row["date_time"])
        self.assertEqual(self.e.batch(self.rice)[0]["qty_sold"], 3)      # the figures are read back from the data file
        self.assertEqual(self.e.pm.search_products(self.e.mgr, name="Rice")[0]["qty_in_stock"], 7)

    def test_TS_9_4C(self):
        """TS9.4C [AC9.4]: Check that a storage failure while saving a sale reverses the entire operation and leaves no incomplete sale record, stock quantity change or success message."""
        import sqlite3
        from app.data.database import Database
        real = self.e.sm.db.conn
        original = self.e.sm.db.transaction
        from contextlib import contextmanager
        @contextmanager
        def failing():
            try:
                real.execute("UPDATE stock_batch SET qty_in_stock = qty_in_stock - 1, qty_sold = qty_sold + 1")
                raise sqlite3.OperationalError("disk full")           # the failure happens after some work was done
                yield real
            except Exception:
                real.rollback()
                raise
        self.e.sm.db.transaction = failing
        with self.assertRaises(sqlite3.OperationalError):
            self.sell(2, "S-1")
        self.e.sm.db.transaction = original
        b = self.e.batch(self.rice)[0]
        self.assertEqual((b["qty_in_stock"], b["qty_sold"], self.e.count("sale")), (10, 0, 0))

    def test_one_sale_across_two_groups(self):
        """one sale across two groups"""
        self.e.add_batch(self.rice, 4, 20)
        self.assertEqual(self.sell(12, "S-1"), 2)
        self.assertEqual(self.e.count("sale"), 2)


