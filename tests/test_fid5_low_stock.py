"""FID-5 Low-stock alert (Ricardo). One test per SRS test scenario (TS-5.x).
NOTE: the SRS wording of TS-5.1A/B and TS-5.3B talks about 'credentials' and 'errors'. These tests check
what the feature actually does (who may see alerts, and that the quantities shown are accurate), so the
SRS rows should be reworded to match - see the docstrings below."""
import unittest

from app.logic.errors import PermissionDenied
from tests.helpers import Env


class Fid5LowStockTests(unittest.TestCase):
    def setUp(self):
        self.e = Env()
        self.addCleanup(self.e.close)
        self.rice = self.e.add("Rice 5kg", 4, 5)        # below the level
        self.sugar = self.e.add("Sugar 2kg", 3, 3)      # exactly at the level
        self.flour = self.e.add("Flour 1kg", 50, 10)    # above the level

    def names(self):
        return {a["name"] for a in self.e.am.low_stock_alerts(self.e.mgr)}

    def test_TS_5_1A(self):
        """TS-5.1A [AC-5.1]: Verify that a signed-in user with permission (inventory manager, owner, warehouse staff) can view the low-stock alerts."""
        for user in (self.e.mgr, self.e.owner, self.e.wh):
            self.assertEqual(len(self.e.am.low_stock_alerts(user)), 2)

    def test_TS_5_1B(self):
        """TS-5.1B [AC-5.1]: Verify that a user who is not signed in, or a sales/cashier user, cannot view the alerts and receives an access denied message."""
        for user in (None, self.e.cash):
            with self.assertRaises(PermissionDenied):
                self.e.am.low_stock_alerts(user)

    def test_TS_5_2A(self):
        """TS-5.2A [AC-5.2]: Verify that each alert shows the product name, In Stock quantity and low-stock level of the matching product."""
        alert = [a for a in self.e.am.low_stock_alerts(self.e.mgr) if a["product_id"] == self.rice][0]
        self.assertEqual((alert["name"], alert["in_stock"], alert["threshold"]), ("Rice 5kg", 4, 5))

    def test_TS_5_2B(self):
        """TS-5.2B [AC-5.2]: Verify that 'Unknown Product' is listed when stock points at a product that does not exist."""
        self.e.db.conn.execute("PRAGMA foreign_keys = OFF")
        self.e.db.conn.execute("INSERT INTO stock_batch(product_id, qty_in_stock) VALUES (999, 2)")
        self.e.db.conn.commit()
        alerts = self.e.am.low_stock_alerts(self.e.mgr)
        self.assertIn(("Unknown Product", 2), [(a["name"], a["in_stock"]) for a in alerts])

    def test_TS_5_3A(self):
        """TS-5.3A [AC-5.3]: Verify that the quantity shown is the sum of In Stock units over all batches of the product."""
        self.e.add_batch(self.rice, 1, 60)
        alert = [a for a in self.e.am.low_stock_alerts(self.e.mgr) if a["product_id"] == self.rice][0]
        self.assertEqual(alert["in_stock"], 5)

    def test_TS_5_3B(self):
        """TS-5.3B [AC-5.3]: Verify that Sold, Damaged and Expired units are NOT counted in the quantity shown."""
        self.e.db.conn.execute("UPDATE stock_batch SET qty_sold = 20, qty_damaged = 20, qty_expired = 20"
                               " WHERE product_id = ?", (self.rice,))
        self.e.db.conn.commit()
        alert = [a for a in self.e.am.low_stock_alerts(self.e.mgr) if a["product_id"] == self.rice][0]
        self.assertEqual(alert["in_stock"], 4)

    def test_TS_5_4A(self):
        """TS-5.4A [AC-5.4]: Verify that low-stock alerts are displayed when stock quantities meet or are below threshold."""
        self.assertEqual(self.names(), {"Rice 5kg", "Sugar 2kg"})              # below AND exactly at the level

    def test_TS_5_4B(self):
        """TS-5.4B [AC-5.4]: Verify normal behaviour if quantities are above threshold (no alert; an alert clears after a top-up)."""
        self.assertNotIn("Flour 1kg", self.names())
        self.e.db.conn.execute("UPDATE stock_batch SET qty_in_stock = 6 WHERE product_id = ?", (self.rice,))
        self.e.db.conn.commit()
        self.assertNotIn("Rice 5kg", self.names())


if __name__ == "__main__":
    unittest.main()
