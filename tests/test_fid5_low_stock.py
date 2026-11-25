"""FID-5 Low-stock alert (Ricardo). One test per SRS test scenario (TS-5.x), worded as in SRS v0.5."""
import time
import unittest

from app.logic.errors import PermissionDenied
from tests.helpers import Env

RECEIVED = "Stock received"


class Fid5LowStockTests(unittest.TestCase):
    def setUp(self):
        self.e = Env()
        self.addCleanup(self.e.close)

    def alerts(self):
        return {a["name"]: a for a in self.e.am.low_stock_alerts(self.e.mgr)}

    def test_TS_5_1A(self):
        """TS-5.1A [AC-5.1]: Verify that a signed-in Warehouse / Stock Staff, Stock / Inventory Manager or Business Owner / Manager user can open the low-stock alert list."""
        self.e.add("Rice 5kg", 4, 5)
        for user in (self.e.wh, self.e.mgr, self.e.owner):
            self.assertEqual(len(self.e.am.low_stock_alerts(user)), 1)

    def test_TS_5_1B(self):
        """TS-5.1B [AC-5.1]: Verify that a Sales / Cashier user, and a user who is not signed in, cannot open the list and receive an access denied message."""
        for user in (self.e.cash, None):
            with self.assertRaises(PermissionDenied):
                self.e.am.low_stock_alerts(user)

    def test_TS_5_2A(self):
        """TS-5.2A [AC-5.2]: Verify that recording damage (FID-10) that takes a product's In Stock quantity to or below its threshold adds its alert within two seconds."""
        pid = self.e.add("Rice 5kg", 10, 5)
        self.assertNotIn("Rice 5kg", self.alerts())
        start = time.time()
        self.e.sm.record_damage(self.e.mgr, pid, 5, "Other")
        found = self.alerts()
        self.assertLess(time.time() - start, 2)
        self.assertEqual((found["Rice 5kg"]["in_stock"], found["Rice 5kg"]["threshold"]), (5, 5))

    def test_TS_5_2B(self):
        """TS-5.2B [AC-5.2]: Verify that raising a product's threshold above its quantity adds an alert, and lowering it below the quantity removes the alert, each within two seconds."""
        pid = self.e.add("Rice 5kg", 10, 5)
        start = time.time()
        self.e.pm.update_product(self.e.mgr, pid, threshold="12")
        self.assertIn("Rice 5kg", self.alerts())
        self.e.pm.update_product(self.e.mgr, pid, threshold="3")
        self.assertNotIn("Rice 5kg", self.alerts())
        self.assertLess(time.time() - start, 2)

    def test_TS_5_3A(self):
        """TS-5.3A [AC-5.3]: Verify that a product with threshold 10 and In Stock quantity 10 is listed with the correct name, quantity and threshold (boundary)."""
        self.e.add("Sugar 2kg", 10, 10)
        a = self.alerts()["Sugar 2kg"]
        self.assertEqual((a["in_stock"], a["threshold"]), (10, 10))

    def test_TS_5_3B(self):
        """TS-5.3B [AC-5.3]: Verify that a product with threshold 10 and quantity 11, and a product with no threshold, are not listed."""
        self.e.add("Flour 1kg", 11, 10)
        self.e.add("Salt 1kg", 0, 0)
        self.assertEqual(self.alerts(), {})

    def test_TS_5_3C(self):
        """TS-5.3C [AC-5.3]: Verify that a product with quantity 0 and a threshold set is listed."""
        self.e.add("Oil 1L", 0, 5)
        self.assertEqual(self.alerts()["Oil 1L"]["in_stock"], 0)

    def test_TS_5_4A(self):
        """TS-5.4A [AC-5.4]: Verify that receiving stock (FID-4) so the quantity rises above the threshold removes the alert with no user action."""
        pid = self.e.add("Rice 5kg", 4, 5)
        self.assertIn("Rice 5kg", self.alerts())
        self.e.sm.change_stock(self.e.mgr, pid, RECEIVED, 10, "delivery")
        self.assertNotIn("Rice 5kg", self.alerts())

    def test_TS_5_4B(self):
        """TS-5.4B [AC-5.4]: Verify that archiving a product that has an alert removes that alert and leaves alerts for other products unchanged."""
        a = self.e.add("Rice 5kg", 4, 5)
        self.e.add("Sugar 2kg", 3, 3)
        self.e.pm.remove_product(self.e.mgr, a, "Discontinued")
        self.assertEqual(set(self.alerts()), {"Sugar 2kg"})


if __name__ == "__main__":
    unittest.main()
