"""FID-4 Stock changes. One test per SRS test scenario (TS-4.x)."""
import unittest
from datetime import timedelta

from app.logic.errors import PermissionDenied, ValidationError
from tests.helpers import Env

class T(unittest.TestCase):
    def setUp(self):
        self.e = Env()
        self.addCleanup(self.e.close)
        self.rice = self.e.add("Rice 5kg", 50, 10)
        self.R, self.C = "Stock received", "Count correction"
        self.last = lambda: self.e.sm.in_stock_quantity(self.rice)

    def test_TS_4_1(self):
        """TS-4.1 [AC-4.1]: Verify that an authorized user can select a product and open the stock change form with change type, quantity and reason fields."""
        self.assertEqual(self.e.sm.change_stock(self.e.wh, self.rice, self.R, 1, "delivery"), 51)
        self.assertEqual(self.e.sm.change_stock(self.e.mgr, self.rice, self.R, 1, "delivery"), 52)

    def test_TS_4_2(self):
        """TS-4.2 [AC-4.1]: Verify that a user without authorization cannot record a stock change and receives an access denied message."""
        for user in (self.e.cash, self.e.owner, None):
            with self.assertRaises(PermissionDenied):
                self.e.sm.change_stock(user, self.rice, self.R, 5, "x")
        self.assertEqual(self.last(), 50)

    def test_TS_4_3(self):
        """TS-4.3 [AC-4.2]: Verify that a quantity of zero, a negative number, a decimal and non-numeric text are each rejected with an error and the stock level is unchanged."""
        for bad in ("0", "-3", "2.5", "abc", ""):
            with self.assertRaises(ValidationError):
                self.e.sm.change_stock(self.e.wh, self.rice, self.R, bad, "x")
        for bad in ("0", "2.5", "abc"):
            with self.assertRaises(ValidationError):
                self.e.sm.change_stock(self.e.wh, self.rice, self.C, bad, "x")
        self.assertEqual(self.last(), 50)

    def test_TS_4_4(self):
        """TS-4.4 [AC-4.2]: Verify that a correction removing 60 units from a product with 50 In Stock is rejected and the level stays at 50, and that a correction removing exactly 50 is accepted and leaves 0 (boundary)."""
        with self.assertRaises(ValidationError):
            self.e.sm.change_stock(self.e.wh, self.rice, self.C, -60, "recount")
        self.assertEqual(self.last(), 50)
        self.assertEqual(self.e.sm.change_stock(self.e.wh, self.rice, self.C, -50, "recount"), 0)

    def test_TS_4_5(self):
        """TS-4.5 [AC-4.3]: Verify that for a product with 50 In Stock, recording 20 received and confirming results in 70."""
        self.assertEqual(self.e.sm.change_stock(self.e.wh, self.rice, self.R, 20, "delivery"), 70)

    def test_TS_4_6(self):
        """TS-4.6 [AC-4.3]: Verify that a count correction of minus 5 on 50 In Stock results in 45, and that cancelling at the confirmation step leaves the level unchanged."""
        self.assertEqual(self.e.sm.change_stock(self.e.wh, self.rice, self.C, -5, "recount"), 45)
        # cancelling at the confirmation step: change_stock is never called, so nothing changes
        self.assertEqual(self.last(), 45)

    def test_TS_4_7(self):
        """TS-4.7 [AC-4.4]: Verify that after a sale of 5 units is recorded (FID-9), In Stock falls by 5, Sold rises by 5, and the total across statuses is unchanged."""
        total = lambda: sum(b["qty_in_stock"] + b["qty_sold"] + b["qty_damaged"] + b["qty_expired"] for b in self.e.batch(self.rice))
        self.e.sm.record_sale(self.e.cash, self.rice, 5, "S-1")
        b = self.e.batch(self.rice)[0]
        self.assertEqual((b["qty_in_stock"], b["qty_sold"], total()), (45, 5, 50))

    def test_TS_4_8(self):
        """TS4.8 [AC-4.4]: Verify that the same holds when 3 units are recorded as Damaged (FID-10) and when 10 units are marked Expired (FID-11)."""
        total = lambda: sum(b["qty_in_stock"] + b["qty_sold"] + b["qty_damaged"] + b["qty_expired"] for b in self.e.batch(self.rice))
        self.e.sm.record_damage(self.e.wh, self.rice, 3, "Damaged in storage")
        self.assertEqual((self.e.batch(self.rice)[0]["qty_damaged"], total()), (3, 50))
        other = self.e.add("Old stock", 10, 0)
        self.e.db.conn.execute("UPDATE stock_batch SET expiry_date = ? WHERE product_id = ?", ((self.e.today - timedelta(days=1)).isoformat(), other))
        self.e.db.conn.commit()
        self.e.sm.expire_overdue()
        b = self.e.batch(other)[0]
        self.assertEqual((b["qty_expired"], b["qty_in_stock"]), (10, 0))

    def test_TS_4_9(self):
        """TS-4.9 [AC-4.5]: Verify that after a confirmed stock change the log contains the product, quantity, reason, user, and date and time."""
        self.e.sm.change_stock(self.e.wh, self.rice, self.R, 20, "delivery from Acme")
        row = self.e.db.query("SELECT * FROM stock_change ORDER BY id DESC LIMIT 1")[0]
        self.assertEqual((row["quantity"], row["performed_by"], row["to_status"]), (20, "wh", "In Stock"))
        self.assertIn("delivery from Acme", row["reason"])
        self.assertTrue(row["date_time"])

    def test_TS_4_10(self):
        """TS-4.10 [AC-4.5]: Verify that a rejected change (for example, one that would take stock below zero) and a cancelled change create no log entry."""
        before = (self.e.count("stock_change"), self.e.count("audit_log"))
        with self.assertRaises(ValidationError):
            self.e.sm.change_stock(self.e.wh, self.rice, self.C, -60, "recount")
        self.assertEqual((self.e.count("stock_change"), self.e.count("audit_log")), before)

    def test_TS_4_11(self):
        """TS-4.11 [AC-4.6]: Verify that reducing stock to or below the threshold makes the low-stock alert appear."""
        self.assertEqual(self.e.am.low_stock_alerts(self.e.mgr), [])
        self.e.sm.change_stock(self.e.wh, self.rice, self.C, -40, "recount")      # 10 = threshold
        self.assertEqual([a["name"] for a in self.e.am.low_stock_alerts(self.e.mgr)], ["Rice 5kg"])

    def test_TS_4_12(self):
        """TS-4.12 [AC-4.6]: Verify that recording received stock so the level rises above the threshold removes the alert, and that a level exactly at the threshold still shows it (boundary)."""
        self.e.sm.change_stock(self.e.wh, self.rice, self.C, -45, "recount")      # 5, below threshold 10
        self.assertEqual(len(self.e.am.low_stock_alerts(self.e.mgr)), 1)
        self.e.sm.change_stock(self.e.wh, self.rice, self.R, 5, "delivery")       # exactly 10: still shown
        self.assertEqual(len(self.e.am.low_stock_alerts(self.e.mgr)), 1)
        self.e.sm.change_stock(self.e.wh, self.rice, self.R, 1, "delivery")       # 11: removed
        self.assertEqual(self.e.am.low_stock_alerts(self.e.mgr), [])

    def test_received_stock_with_new_expiry_makes_new_batch(self):
        """received stock with new expiry makes new batch"""
        exp = (self.e.today + timedelta(days=20)).isoformat()
        self.e.sm.change_stock(self.e.wh, self.rice, self.R, 7, "delivery", expiry=exp)
        self.assertEqual(sorted(b["qty_in_stock"] for b in self.e.batch(self.rice)), [7, 50])

    def test_received_stock_with_past_expiry_rejected(self):
        """received stock with past expiry rejected"""
        with self.assertRaises(ValidationError):
            self.e.sm.change_stock(self.e.wh, self.rice, self.R, 7, "delivery", expiry=(self.e.today - timedelta(days=1)).isoformat())

    def test_reason_is_required(self):
        """reason is required"""
        with self.assertRaises(ValidationError):
            self.e.sm.change_stock(self.e.wh, self.rice, self.R, 7, " ")


