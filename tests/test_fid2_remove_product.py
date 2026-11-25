"""FID-2 Remove product. One test per SRS test scenario (TS-2.x)."""
import unittest
from datetime import timedelta

from app.logic.errors import PermissionDenied, ValidationError
from tests.helpers import Env

class T(unittest.TestCase):
    def setUp(self):
        self.e = Env()
        self.addCleanup(self.e.close)
        self.rice = self.e.add("Rice 5kg", 10, 3)
        self.rice2 = self.e.add("Basmati Rice", 4, 3)

    def test_TS_2_1A(self):
        """TS-2.1A [AC-2.1]: Verify that an authorized user can access the remove product option."""
        info = self.e.pm.removal_summary(self.e.mgr, self.rice)
        self.assertEqual(info["name"], "Rice 5kg")
        self.assertEqual(self.e.pm.removal_summary(self.e.owner, self.rice)["quantity"], 10)

    def test_TS_2_1B(self):
        """TS-2.1B [AC-2.1]: Verify that a user without authorization cannot access the remove product option or remove a product and receives an access denied message."""
        for user in (self.e.cash, self.e.wh, None):
            with self.assertRaises(PermissionDenied):
                self.e.pm.removal_summary(user, self.rice)
            with self.assertRaises(PermissionDenied):
                self.e.pm.remove_product(user, self.rice, "x")
        self.assertEqual(len(self.e.pm.list_products(self.e.mgr)), 2)

    def test_TS_2_2A(self):
        """TS-2.2A [AC-2.2]: Verify that a user can select an existing product, and the system recognizes that it exists."""
        self.assertEqual(self.e.pm.removal_summary(self.e.mgr, self.rice)["product_id"], self.rice)

    def test_TS_2_2B(self):
        """TS-2.2B [AC-2.2]: Verify that attempting to remove a product that has already been removed (for example, by another user) displays an error and changes nothing."""
        self.e.pm.remove_product(self.e.mgr, self.rice, "discontinued")
        before = self.e.count("audit_log")
        with self.assertRaises(ValidationError):
            self.e.pm.remove_product(self.e.owner, self.rice, "again")
        self.assertEqual(self.e.count("audit_log"), before)
        self.assertEqual(len(self.e.pm.list_products(self.e.mgr)), 1)

    def test_TS_2_3A(self):
        """TS-2.3A [AC-2.3]: Verify that a confirmation prompt showing the product name and current quantity is displayed when the user chooses to remove a product. The prompt also asks for a reason."""
        info = self.e.pm.removal_summary(self.e.mgr, self.rice)       # what the confirmation prompt shows
        self.assertEqual((info["name"], info["quantity"]), ("Rice 5kg", 10))
        with self.assertRaises(ValidationError) as ctx:               # the prompt also asks for a reason
            self.e.pm.remove_product(self.e.mgr, self.rice, "  ")
        self.assertIn("reason", ctx.exception.errors)

    def test_TS_2_3B(self):
        """TS-2.3B [AC-2.3]: Verify that the product is not removed while the confirmation prompt is still open and unanswered."""
        self.e.pm.removal_summary(self.e.mgr, self.rice)              # prompt open, not yet answered
        self.assertIn("Rice 5kg", [r["name"] for r in self.e.pm.list_batches(self.e.mgr)])

    def test_TS_2_4A(self):
        """TS-2.4A [AC-2.4]: Verify that after confirming, the product is no longer returned when searched by name."""
        self.e.pm.remove_product(self.e.mgr, self.rice, "discontinued")
        self.assertEqual(self.e.pm.search_products(self.e.mgr, name="Rice 5kg"), [])

    def test_TS_2_4B(self):
        """TS-2.4B [AC-2.4]: Verify that removing a product that had a low stock or nearing expiry notification also removes that notification."""
        self.e.pm.remove_product(self.e.mgr, self.rice, "discontinued")      # Rice 5kg (10) is above its level 3, so use a low product
        low = self.e.add("Sugar", 1, 5, days=5)
        self.assertEqual([a["name"] for a in self.e.am.low_stock_alerts(self.e.mgr)], ["Sugar"])
        self.assertEqual(len(self.e.am.nearing_expiry_notifications(self.e.mgr)), 1)
        self.e.pm.remove_product(self.e.mgr, low, "discontinued")
        self.assertEqual(self.e.am.low_stock_alerts(self.e.mgr), [])
        self.assertEqual(self.e.am.nearing_expiry_notifications(self.e.mgr), [])

    def test_TS_2_4C(self):
        """TS-2.4C [AC-2.4]: Verify that removing one product does not affect any other product record (for example, a product with a similar name)."""
        self.e.pm.remove_product(self.e.mgr, self.rice, "discontinued")
        self.assertEqual([r["name"] for r in self.e.pm.list_batches(self.e.mgr)], ["Basmati Rice"])
        self.assertEqual(self.e.batch(self.rice2)[0]["qty_in_stock"], 4)

    def test_TS_2_5A(self):
        """TS-2.5A [AC-2.5]: Verify that a confirmation message is displayed after a successful removal."""
        self.assertEqual(self.e.pm.remove_product(self.e.mgr, self.rice, "discontinued"), "Rice 5kg")   # the screen shows this in its message
        self.assertEqual(self.e.db.query("SELECT action FROM audit_log ORDER BY id DESC LIMIT 1")[0]["action"], "remove_product")

    def test_TS_2_5B(self):
        """TS-2.5B [AC-2.5]: Verify that when the user cancels the confirmation prompt, the product and its quantity remain unchanged."""
        self.e.pm.removal_summary(self.e.mgr, self.rice)              # the user opens the prompt and cancels: remove_product is never called
        self.assertEqual(self.e.batch(self.rice)[0]["qty_in_stock"], 10)
        self.assertEqual(len(self.e.pm.list_products(self.e.mgr)), 2)

    def test_TS_2_5C(self):
        """TS-2.5C [AC-2.5]: Verify that when the removal fails (for example, loss of the database connection), an error is displayed and the product remains in the inventory."""
        import sqlite3
        from contextlib import contextmanager
        @contextmanager
        def broken():
            raise sqlite3.OperationalError("database connection lost")
            yield
        self.e.pm.db.transaction = broken
        with self.assertRaises(sqlite3.OperationalError):
            self.e.pm.remove_product(self.e.mgr, self.rice, "discontinued")
        self.assertEqual(len(self.e.pm.list_products(self.e.mgr)), 2)

    def test_name_is_free_again_after_removal(self):
        """name is free again after removal"""
        self.e.pm.remove_product(self.e.mgr, self.rice, "discontinued")
        self.e.pm.add_product(self.e.mgr, "Rice 5kg", 3)
        self.assertEqual(len(self.e.pm.list_products(self.e.mgr)), 2)

    def test_stock_history_is_kept(self):
        """stock history is kept"""
        self.e.pm.remove_product(self.e.mgr, self.rice, "discontinued")
        self.assertGreaterEqual(self.e.count("stock_change"), 1)


