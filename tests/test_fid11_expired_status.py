"""FID-11 Expired status (Janae). One test per SRS test scenario (TS-11.x)."""
import unittest
from datetime import timedelta

from tests.helpers import Env


class Fid11ExpiredStatusTests(unittest.TestCase):
    def setUp(self):
        self.e = Env()
        self.addCleanup(self.e.close)

    def test_TS_11_1A(self):
        """TS-11.1A [AC-11.1]: Verify that an In Stock quantity with an expiry date of yesterday changes to Expired."""
        pid = self.e.add("Juice", 12, 4, -1)
        self.assertEqual(self.e.sm.expire_overdue(), 12)
        self.assertEqual(self.e.status(pid), ["Expired"])
        b = self.e.batch(pid)[0]
        self.assertEqual((b["qty_in_stock"], b["qty_expired"]), (0, 12))
        log = self.e.db.query("SELECT * FROM audit_log WHERE action = 'expire_stock'")[0]
        self.assertIsNone(log["performed_by"])                               # automatic event (SEC-4)

    def test_TS_11_1C(self):
        """TS-11.1C [AC-11.1]: Verify that when several products are past their expiry date, all of their expired quantities change to Expired."""
        ids = [self.e.add("A", 3, 1, -1), self.e.add("B", 4, 1, -10), self.e.add("C", 5, 1, -30)]
        self.assertEqual(self.e.sm.expire_overdue(), 12)
        self.assertEqual([self.e.status(p) for p in ids], [["Expired"]] * 3)

    def test_TS_11_2A(self):
        """TS-11.2A [AC-11.2]: Verify that stock expiring today stays In Stock."""
        pid = self.e.add("Butter", 9, 2, 0)
        self.assertEqual(self.e.sm.expire_overdue(), 0)
        self.assertEqual(self.e.status(pid), ["In Stock"])
        self.assertEqual(self.e.batch(pid)[0]["qty_in_stock"], 9)

    def test_TS_11_2B(self):
        """TS-11.2B [AC-11.2]: Verify that the same stock changes to Expired the next day."""
        pid = self.e.add("Butter", 9, 2, 0)
        self.e.sm.expire_overdue()
        self.e.today += timedelta(days=1)                                    # the clock moves to tomorrow
        self.assertEqual(self.e.sm.expire_overdue(), 9)
        self.assertEqual(self.e.status(pid), ["Expired"])

    def test_TS_11_3A(self):
        """TS-11.3A [AC-11.3]: Verify that In Stock quantity with no expiry date stays In Stock."""
        pid = self.e.add("Flour", 50, 10)
        self.assertEqual(self.e.sm.expire_overdue(), 0)
        self.assertEqual(self.e.status(pid), ["In Stock"])

    def test_TS_11_3B(self):
        """TS-11.3B [AC-11.3]: Verify that stock with no expiry date is left alone when other stock with passed dates is marked Expired."""
        flour = self.e.add("Flour", 50, 10)
        juice = self.e.add("Juice", 12, 4, -2)
        self.assertEqual(self.e.sm.expire_overdue(), 12)
        self.assertEqual((self.e.status(flour), self.e.status(juice)), (["In Stock"], ["Expired"]))
        self.assertEqual(self.e.batch(flour)[0]["qty_in_stock"], 50)

    def test_TS_11_4A(self):
        """TS-11.4A [AC-11.4]: Verify that a Damaged quantity with a passed expiry date stays Damaged."""
        pid = self.e.add("Milk", 5, 1, 3)
        self.e.sm.record_damage(self.e.mgr, pid, 5, "Other")
        self.e.today += timedelta(days=10)                                   # its expiry date has now passed
        self.assertEqual(self.e.sm.expire_overdue(), 0)
        self.assertEqual(self.e.status(pid), ["Damaged"])
        b = self.e.batch(pid)[0]
        self.assertEqual((b["qty_damaged"], b["qty_expired"]), (5, 0))

    def test_TS_11_4B(self):
        """TS-11.4B [AC-11.4]: Verify that a Sold quantity with a passed expiry date stays Sold."""
        pid = self.e.add("Milk", 5, 1, -3)
        self.e.db.conn.execute("UPDATE stock_batch SET qty_in_stock = 0, qty_sold = 5 WHERE product_id = ?", (pid,))
        self.e.db.conn.commit()                                              # (sales are a separate feature)
        self.e.db.conn.execute("INSERT INTO stock_change(batch_id, quantity, from_status, to_status, reason,"
                               " performed_by, date_time) VALUES (?,5,'In Stock','Sold','Sale','cash','now')",
                               (self.e.batch(pid)[0]["id"],))
        self.e.db.conn.commit()
        self.assertEqual(self.e.sm.expire_overdue(), 0)
        self.assertEqual(self.e.status(pid), ["Sold"])
        self.assertEqual(self.e.batch(pid)[0]["qty_expired"], 0)

    def test_TS_11_5A(self):
        """TS-11.5A [AC-11.5]: Verify that after a check that expires stock, the audit record shows the product, quantity moved, expiry date, date and time."""
        self.e.add("Juice", 12, 4, -2)
        self.e.sm.expire_overdue()
        log = self.e.db.query("SELECT * FROM audit_log WHERE action = 'expire_stock'")
        self.assertEqual(len(log), 1)
        self.assertIsNone(log[0]["performed_by"])
        self.assertIn("Juice", log[0]["detail"])
        self.assertIn("12", log[0]["detail"])
        self.assertTrue(log[0]["date_time"])
        self.assertRegex(log[0]["detail"], r"\d{4}-\d{2}-\d{2}")                # the expiry date

    def test_TS_11_1B(self):
        """TS-11.1B [AC-11.1]: Verify that for a product with 6 units that expired yesterday and 4 units expiring in 10 days, only the 6 move to Expired and the 4 stay In Stock."""
        pid = self.e.add("Juice", 6, 2, -1)
        self.e.add_batch(pid, 4, 10)
        self.assertEqual(self.e.sm.expire_overdue(), 6)
        b = self.e.batch(pid)
        self.assertEqual([(x["qty_in_stock"], x["qty_expired"]) for x in b], [(0, 6), (4, 0)])

    def test_TS_11_4C(self):
        """TS-11.4C [AC-11.4]: Verify that after an expiry check the total across In Stock, Sold, Damaged and Expired is unchanged."""
        pid = self.e.add("Juice", 20, 2, -1)
        self.e.db.conn.execute("UPDATE stock_batch SET qty_in_stock = 12, qty_sold = 3, qty_damaged = 5 WHERE product_id = ?", (pid,))
        self.e.db.conn.commit()
        def total():
            b = self.e.batch(pid)[0]
            return b["qty_in_stock"] + b["qty_sold"] + b["qty_damaged"] + b["qty_expired"]
        before = total()
        self.e.sm.expire_overdue()
        self.assertEqual(total(), before)
        self.assertEqual(self.e.batch(pid)[0]["qty_expired"], 12)

    def test_TS_11_5B(self):
        """TS-11.5B [AC-11.5]: Verify that a check that changes nothing creates no audit record."""
        self.e.add("Flour", 50, 10)
        self.e.add("Butter", 9, 2, 5)
        self.assertEqual(self.e.sm.expire_overdue(), 0)
        self.assertEqual(self.e.db.query("SELECT * FROM audit_log WHERE action = 'expire_stock'"), [])

    def test_all_or_nothing(self):
        a = self.e.add("A", 3, 1, -1)
        self.e.add("B", 4, 1, -1)
        self.e.db.conn.execute("DROP TABLE audit_log")                       # make the save fail part-way
        with self.assertRaises(Exception):
            self.e.sm.expire_overdue()
        self.assertEqual(self.e.batch(a)[0]["qty_in_stock"], 3)              # nothing was changed


if __name__ == "__main__":
    unittest.main()
