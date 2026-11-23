"""FID-6 Nearing-expiry notification (Tevin). One test per SRS test scenario (TS6.x)."""
import unittest

from app.logic.expiry_timer import ExpiryTimer
from tests.helpers import Env


class FakeRoot:
    """Stands in for tkinter's after()/after_cancel() so the timer can be tested without a window."""
    def __init__(self):
        self.scheduled = []

    def after(self, ms, func):
        self.scheduled.append((ms, func))
        return len(self.scheduled)

    def after_cancel(self, job):
        pass


class Fid6NearingExpiryTests(unittest.TestCase):
    def setUp(self):
        self.e = Env()
        self.addCleanup(self.e.close)

    def notes(self):
        return self.e.am.nearing_expiry_notifications(self.e.mgr)

    def test_alerts_are_not_shown_to_cashiers(self):
        """SR6.3: only warehouse staff, inventory managers and owners see the notifications."""
        from app.logic.errors import PermissionDenied
        for user in (self.e.mgr, self.e.owner, self.e.wh):
            self.e.am.nearing_expiry_notifications(user)
        for user in (self.e.cash, None):
            with self.assertRaises(PermissionDenied):
                self.e.am.nearing_expiry_notifications(user)

    def test_TS6_1A(self):
        """TS6.1A [AC6.1]: Check that at least one expiry check finishes successfully during a continuous period of 24 hours while the application is running."""
        root = FakeRoot()
        timer = ExpiryTimer(root, self.e.sm)
        timer.start()
        self.assertEqual(root.scheduled[0][0], 24 * 60 * 60 * 1000)         # next check is queued 24 h later

    def test_TS6_1B(self):
        """TS6.1B [AC6.1]: Check that, after more than 24 hours offline, the application completes the overdue expiry check at start-up, before the stock is used."""
        pid = self.e.add("Juice 1L", 12, 4, -2)                              # expired while the app was off
        ExpiryTimer(FakeRoot(), self.e.sm).start()                           # start-up runs the check at once
        self.assertEqual((self.e.batch(pid)[0]["qty_in_stock"], self.e.batch(pid)[0]["qty_expired"]), (0, 12))

    def test_TS6_2A(self):
        """TS6.2A [AC6.2]: Check that eligible stock with exactly 30 days left before expiry receives a Nearing Expiry flag and remains In Stock."""
        pid = self.e.add("Yogurt", 8, 2, 30)
        self.assertEqual([n["product_id"] for n in self.notes()], [pid])
        self.assertEqual(self.e.status(pid), ["In Stock"])

    def test_TS6_2B(self):
        """TS6.2B [AC6.2]: Check that eligible stock expiring in seven days receives a Nearing Expiry flag and remains In Stock."""
        pid = self.e.add("Milk", 20, 5, 7)
        self.assertEqual([n["days_left"] for n in self.notes()], [7])
        self.assertEqual(self.e.status(pid), ["In Stock"])

    def test_TS6_2C(self):
        """TS6.2C [AC6.2]: Check that eligible stock expiring today receives a Nearing Expiry flag under the proposed rule for expiry at the end of the day."""
        self.e.add("Butter", 9, 2, 0)
        self.assertEqual([n["days_left"] for n in self.notes()], [0])

    def test_TS6_2D(self):
        """TS6.2D [AC6.2]: Check that stock expiring in 31 days does not receive a Nearing Expiry flag."""
        self.e.add("Cheese", 6, 2, 31)
        self.assertEqual(self.notes(), [])

    def test_TS6_2E(self):
        """TS6.2E [AC6.2]: Check that stock which expired yesterday is shown as Expired rather than Nearing Expiry."""
        pid = self.e.add("Cream", 5, 2, -1)
        self.assertEqual(self.notes(), [])
        self.e.sm.expire_overdue()
        self.assertEqual(self.e.status(pid), ["Expired"])

    def test_TS6_3A(self):
        """TS6.3A [AC6.3]: Compare a flagged product's notification with its saved record and confirm that the name, eligible quantity and expiry date are correct."""
        self.e.add("Milk 1L", 20, 5, 10)
        n = self.notes()[0]
        self.assertEqual((n["name"], n["quantity"], n["expiry_date"]), ("Milk 1L", 20, "2026-12-03"))

    def test_TS6_3B(self):
        """TS6.3B [AC6.3]: Check that notifications for several products or separate expiry groups remain clearly identifiable. A saved quantity change or expiry date correction must update the affected notification without changing unrelated notifications."""
        milk = self.e.add("Milk 1L", 20, 5, 10)
        yog = self.e.add("Yogurt", 8, 2, 20)
        self.e.add_batch(milk, 4, 25)                                         # a second expiry group for Milk
        self.assertEqual([(n["name"], n["quantity"]) for n in self.notes()],
                         [("Milk 1L", 20), ("Yogurt", 8), ("Milk 1L", 4)])
        self.e.sm.record_damage(self.e.mgr, yog, 3, "Other")                  # quantity change
        self.e.pm.update_product(self.e.mgr, milk, expiry="2026-12-01", batch_id=self.e.batch(milk)[0]["id"])
        self.assertEqual([(n["name"], n["quantity"], n["expiry_date"]) for n in self.notes()],
                         [("Milk 1L", 20, "2026-12-01"), ("Yogurt", 5, "2026-12-13"), ("Milk 1L", 4, "2026-12-18")])

    def test_TS6_4A(self):
        """TS6.4A [AC6.4]: Check that stock without an expiry date produces no nearing expiry notification."""
        self.e.add("Flour", 50, 10)
        self.assertEqual(self.notes(), [])

    def test_TS6_4B(self):
        """TS6.4B [AC6.4]: Check that Damaged stock produces no nearing expiry notification, even when its expiry date is within 30 days."""
        pid = self.e.add("Milk", 5, 2, 10)
        self.e.sm.record_damage(self.e.mgr, pid, 5, "Other")
        self.assertEqual(self.notes(), [])

    def test_TS6_4C(self):
        """TS6.4C [AC6.4]: Check that Sold stock produces no nearing expiry notification, even when its expiry date is within 30 days."""
        pid = self.e.add("Milk", 5, 2, 10)
        self.e.db.conn.execute("UPDATE stock_batch SET qty_in_stock = 0, qty_sold = 5 WHERE product_id = ?", (pid,))
        self.e.db.conn.commit()                                               # (sales are a separate feature)
        self.assertEqual(self.notes(), [])

    def test_TS6_4D(self):
        """TS6.4D [AC6.4]: Check that Expired stock, archived products and groups with no eligible units produce no notification. When the last eligible units in a flagged group are sold or damaged, its warning must disappear while warnings for other eligible groups remain visible."""
        expired = self.e.add("Old", 3, 1, -5)
        self.e.sm.expire_overdue()
        archived = self.e.add("Archived", 3, 1, 5)
        self.e.db.conn.execute("UPDATE product SET archived = 1 WHERE id = ?", (archived,))
        a = self.e.add("A", 4, 1, 5)
        b = self.e.add("B", 4, 1, 6)
        self.e.db.conn.commit()
        self.assertEqual({n["name"] for n in self.notes()}, {"A", "B"})
        self.e.sm.record_damage(self.e.mgr, a, 4, "Other")                    # last units of A gone
        self.assertEqual({n["name"] for n in self.notes()}, {"B"})


if __name__ == "__main__":
    unittest.main()
