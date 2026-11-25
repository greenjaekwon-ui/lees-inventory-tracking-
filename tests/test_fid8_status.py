"""FID-8 Product status. One test per SRS test scenario (TS-8.x)."""
import unittest
from datetime import timedelta

from app.logic.errors import PermissionDenied, ValidationError
from tests.helpers import Env

class T(unittest.TestCase):
    def setUp(self):
        self.e = Env()
        self.addCleanup(self.e.close)
        self.rice = self.e.add("Rice 5kg", 10, 3)

    def test_TS_8_1A(self):
        """TS-8.1A [AC-8.1]: Verify that a product added with a quantity of 1 shows as In Stock."""
        pid = self.e.add("Beans", 1)
        self.assertEqual(self.e.status(pid), ["In Stock"])

    def test_TS_8_1B(self):
        """TS-8.1B [AC-8.1]: Verify that a product added with a quantity of 0 does not show as In Stock."""
        pid = self.e.add("Beans", 0)
        self.assertNotEqual(self.e.status(pid), ["In Stock"])
        self.assertEqual(self.e.status(pid), ["Out of Stock"])

    def test_TS_8_2A(self):
        """TS-8.2A [AC-8.2]: Verify that a product marked Sold no longer shows as In Stock."""
        self.e.sm.record_sale(self.e.cash, self.rice, 10, "S-1")
        self.assertEqual(self.e.status(self.rice), ["Sold"])

    def test_TS_8_2B(self):
        """TS-8.2B [AC-8.2]: Verify that a product marked Damaged or no longer shows as In Stock."""
        self.e.sm.record_damage(self.e.wh, self.rice, 10, "Damaged in storage")
        self.assertEqual(self.e.status(self.rice), ["Damaged"])

    def test_TS_8_2C(self):
        """TS-8.2C [AC-8.2]: Verify that a product marked Expired no longer shows as In Stock."""
        self.e.db.conn.execute("UPDATE stock_batch SET expiry_date = ? WHERE product_id = ?",
                               ((self.e.today - timedelta(days=1)).isoformat(), self.rice))
        self.e.db.conn.commit()
        self.e.sm.expire_overdue()
        self.assertEqual(self.e.status(self.rice), ["Expired"])

    def test_TS_8_3A(self):
        """TS-8.3A [AC-8.3]: Verify that searching for an existing In Stock product shows the In Stock status along with its quantity."""
        row = self.e.pm.search_products(self.e.mgr, name="Rice")[0]
        self.assertEqual((row["status"], row["qty_in_stock"]), ("In Stock", 10))
        self.assertEqual(len(self.e.pm.search_products(self.e.mgr, status="In Stock")), 1)

    def test_TS_8_3B(self):
        """TS-8.3B [AC-8.3]: Verify that searching for a product that is not In Stock shows its actual status and not In Stock."""
        self.e.sm.record_damage(self.e.wh, self.rice, 10, "Damaged in storage")
        row = self.e.pm.search_products(self.e.mgr, name="Rice")[0]
        self.assertEqual(row["status"], "Damaged")
        self.assertEqual(self.e.pm.search_products(self.e.mgr, status="In Stock"), [])

    def test_partial_sale_keeps_in_stock(self):
        """partial sale keeps in stock"""
        self.e.sm.record_sale(self.e.cash, self.rice, 3, "S-1")
        self.assertEqual(self.e.status(self.rice), ["In Stock"])


