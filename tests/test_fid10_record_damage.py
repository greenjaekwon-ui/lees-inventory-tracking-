"""FID-10 Record damaged product (D'mitri). One test per SRS test scenario (TS-10.x).
Checks that need a real window (values kept on the form, the confirmation pop-up) are noted as 'by hand'."""
import time
import unittest

from app.logic.errors import PermissionDenied, ValidationError
from app.logic.models import DamageReason
from tests.helpers import Env

REASON = DamageReason.IN_STORAGE.value


class Fid10RecordDamageTests(unittest.TestCase):
    def setUp(self):
        self.e = Env()
        self.addCleanup(self.e.close)
        self.rice = self.e.add("Rice 5kg", 10, 3)

    def damage(self, qty, reason=REASON, note="", pid="rice", user=None):
        pid = self.rice if pid == "rice" else pid
        return self.e.sm.record_damage(user or self.e.wh, pid, qty, reason, note)

    def in_stock(self):
        return self.e.batch(self.rice)[0]["qty_in_stock"]

    def test_TS_10_1A(self):
        """TS-10.1A [AC-10.1]: Verify that a logged-in Warehouse/Stock Staff user and a logged-in Stock/Inventory Manager user can open the Record Damaged Product form."""
        self.assertEqual(self.damage(1, user=self.e.wh), 9)
        self.assertEqual(self.damage(1, user=self.e.mgr), 8)

    def test_TS_10_1B(self):
        """TS-10.1B [AC-10.1]: Verify that a Sales/Cashier user, and a user who is not logged in, cannot access the form and receive an access denied message."""
        for user in (self.e.cash, None):
            with self.assertRaises(PermissionDenied):
                self.e.sm.record_damage(user, self.rice, 1, REASON)
        self.assertEqual(self.in_stock(), 10)

    @unittest.skip("Manual (GUI): values stay on the form until submission - check by hand")
    def test_TS_10_2A(self):
        """TS-10.2A [AC-10.2]: Verify that a user can select an existing product and enter a damaged quantity, a reason and a note, and that the values are retained until submission."""

    def test_TS_10_2B(self):
        """TS-10.2B [AC-10.2]: Verify that an entry with the note left blank can be submitted."""
        self.assertEqual(self.damage(2, note=""), 8)

    def test_TS_10_3A(self):
        """TS-10.3A [AC-10.3]: Verify that an entry with no product selected, or no reason selected, is rejected and an error is displayed on each missing field."""
        with self.assertRaises(ValidationError) as ctx:
            self.damage(1, reason="", pid=None)
        self.assertEqual(set(ctx.exception.errors), {"product", "reason"})
        self.assertEqual(self.in_stock(), 10)

    def test_TS_10_3B(self):
        """TS-10.3B [AC-10.3]: Verify that a damaged quantity that is negative, decimal, non-numeric or 0 is rejected, and that a quantity of 1 is accepted (boundary)."""
        for bad in ("-1", "2.5", "abc", "0", ""):
            with self.assertRaises(ValidationError, msg=bad) as ctx:
                self.damage(bad)
            self.assertIn("quantity", ctx.exception.errors)
        self.assertEqual(self.damage(1), 9)                                  # boundary

    def test_TS_10_3C(self):
        """TS-10.3C [AC-10.3]: Verify that a damaged quantity greater than the product’s current quantity is rejected, and that a damaged quantity equal to the current quantity is accepted (boundary)."""
        with self.assertRaises(ValidationError) as ctx:
            self.damage(11)
        self.assertIn("quantity", ctx.exception.errors)
        self.assertEqual(self.in_stock(), 10)
        self.assertEqual(self.damage(10), 0)                                 # boundary

    def test_TS_10_3D(self):
        """TS-10.3D [AC-10.3]: Verify that an entry for a product with the status Sold, Damaged or Expired is rejected with an error message."""
        sold = self.e.add("Sold item", 5)
        dmg = self.e.add("Damaged item", 5)
        exp = self.e.add("Expired item", 5)
        self.e.db.conn.execute("UPDATE stock_batch SET qty_in_stock=0, qty_sold=5 WHERE product_id=?", (sold,))
        self.e.db.conn.execute("UPDATE stock_batch SET qty_in_stock=0, qty_damaged=5 WHERE product_id=?", (dmg,))
        self.e.db.conn.execute("UPDATE stock_batch SET qty_in_stock=0, qty_expired=5 WHERE product_id=?", (exp,))
        self.e.db.conn.commit()
        for pid in (sold, dmg, exp):
            with self.assertRaises(ValidationError) as ctx:
                self.damage(1, pid=pid)
            self.assertIn("product", ctx.exception.errors)

    def test_TS_10_3E(self):
        """TS-10.3E [AC-10.3]: Verify that a note of exactly 200 characters is accepted and a note of 201 characters is rejected (boundary)."""
        with self.assertRaises(ValidationError) as ctx:
            self.damage(1, note="x" * 201)
        self.assertIn("note", ctx.exception.errors)
        self.assertEqual(self.damage(1, note="x" * 200), 9)

    def test_TS_10_4A(self):
        """TS-10.4A [AC-10.4]: Verify that recording 3 damaged units for a product with a quantity of 10 changes its quantity to 7."""
        self.assertEqual(self.damage(3), 7)
        b = self.e.batch(self.rice)[0]
        self.assertEqual((b["qty_in_stock"], b["qty_damaged"]), (7, 3))

    def test_TS_10_4B(self):
        """TS-10.4B [AC-10.4]: Verify that a rejected entry leaves the product’s quantity unchanged."""
        with self.assertRaises(ValidationError):
            self.damage(99)
        b = self.e.batch(self.rice)[0]
        self.assertEqual((b["qty_in_stock"], b["qty_damaged"]), (10, 0))

    def test_TS_10_4C(self):
        """TS-10.4C [AC-10.4]: Verify that searching for the product within 2 seconds of saving shows the reduced quantity."""
        start = time.monotonic()
        self.damage(3)
        row = [r for r in self.e.pm.list_batches(self.e.mgr) if r["product_id"] == self.rice][0]
        self.assertEqual(row["qty_in_stock"], 7)
        self.assertLess(time.monotonic() - start, 2)

    def test_TS_10_5A(self):
        """TS-10.5A [AC-10.5]: Verify that recording damage for all 4 units of a product with a quantity of 4 sets its status to Damaged and its quantity to 0."""
        pid = self.e.add("Sugar", 4, 1)
        self.assertEqual(self.damage(4, pid=pid), 0)
        self.assertEqual(self.e.status(pid), ["Damaged"])

    def test_TS_10_5B(self):
        """TS-10.5B [AC-10.5]: Verify that recording 1 damaged unit for a product with a quantity of 4 leaves its status as In Stock with a quantity of 3."""
        pid = self.e.add("Sugar", 4, 1)
        self.assertEqual(self.damage(1, pid=pid), 3)
        self.assertEqual(self.e.status(pid), ["In Stock"])

    def test_TS_10_6A(self):
        """TS-10.6A [AC-10.6]: Verify that a valid entry creates exactly one damage record containing the product name, quantity, reason, note, date and time, and username."""
        self.damage(3, note="Torn bag")
        recs = self.e.db.query("SELECT d.*, p.name FROM damage_record d JOIN stock_batch b ON b.id = d.batch_id"
                               " JOIN product p ON p.id = b.product_id")
        self.assertEqual(len(recs), 1)
        r = recs[0]
        self.assertEqual((r["name"], r["quantity"], r["reason"], r["note"], r["performed_by"]),
                         ("Rice 5kg", 3, REASON, "Torn bag", "wh"))
        self.assertTrue(r["date_time"])

    def test_TS_10_6B(self):
        """TS-10.6B [AC-10.6]: Verify that a rejected entry creates no damage record."""
        with self.assertRaises(ValidationError):
            self.damage(0)
        self.assertEqual(self.e.count("damage_record"), 0)
        self.assertEqual(self.e.count("stock_change"), 1)                    # only the 'stock received' row

    @unittest.skip("Manual (GUI): the pop-up text - check by hand (remaining quantity is tested in TS-10.4A)")
    def test_TS_10_7A(self):
        """TS-10.7A [AC-10.7]: Verify that after a successful save a confirmation message shows the product name, damaged quantity and remaining quantity."""

    def test_TS_10_7B(self):
        """TS-10.7B [AC-10.7]: Verify that when the save fails (for example, the database is unavailable) an error message is shown, the quantity, status and damage records are unchanged, and the entered data remains on the form."""
        self.e.db.conn.execute("DROP TABLE audit_log")                       # make the last step of the save fail
        with self.assertRaises(Exception):
            self.damage(3)
        self.assertEqual(self.in_stock(), 10)
        self.assertEqual(self.e.count("damage_record"), 0)
        # (the entered data staying on the form is a screen behaviour - check by hand)

    def test_oldest_expiry_batch_is_used_first(self):
        self.e.add_batch(self.rice, 5, 5)                                    # expires sooner than the first batch
        self.damage(7)
        first, second = self.e.batch(self.rice)
        self.assertEqual((first["qty_in_stock"], second["qty_in_stock"]), (8, 0))
        self.assertEqual((first["qty_damaged"], second["qty_damaged"]), (2, 5))


if __name__ == "__main__":
    unittest.main()
