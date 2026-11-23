"""FID-3 Update Product (Brandon). One test per SRS test scenario (TS-3.x)."""
import unittest

from app.logic.errors import DuplicateProductError, PermissionDenied, ValidationError
from tests.helpers import Env


class Fid3UpdateProductTests(unittest.TestCase):
    def setUp(self):
        self.e = Env()
        self.addCleanup(self.e.close)
        self.rice = self.e.add("Rice 5kg", 10, 5, 40)
        self.flour = self.e.add("Flour 1kg", 20, 4)             # no expiry date

    def saved_row(self, pid):
        return self.e.db.query("SELECT name, low_stock_level FROM product WHERE id = ?", (pid,))[0]

    def test_TS_3_1(self):
        """TS-3.1 [AC-3.1]: Verify that an authorized user can open the update screen for a product."""
        for user in (self.e.mgr, self.e.owner):
            self.assertEqual(self.e.pm.get_product_details(user, self.rice)["name"], "Rice 5kg")

    def test_TS_3_2(self):
        """TS-3.2 [AC-3.1]: Verify that a user without authorization, or a user who is not signed in, cannot access the update screen and receives an access denied message."""
        for user in (self.e.cash, self.e.wh, None):
            with self.assertRaises(PermissionDenied):
                self.e.pm.get_product_details(user, self.rice)
            with self.assertRaises(PermissionDenied):
                self.e.pm.update_product(user, self.rice, name="Hacked")
        self.assertEqual(self.saved_row(self.rice)["name"], "Rice 5kg")

    def test_TS_3_3(self):
        """TS-3.3 [AC-3.2]: Verify that the details shown for a selected product match its saved record."""
        d = self.e.pm.get_product_details(self.e.mgr, self.rice)
        self.assertEqual((d["name"], d["threshold"], d["expiry_date"]), ("Rice 5kg", 5, "2027-01-02"))

    def test_TS_3_4(self):
        """TS-3.4 [AC-3.2]: Verify that a product with no expiry date displays a blank expiry field, with no error or incorrect date."""
        self.assertIsNone(self.e.pm.get_product_details(self.e.mgr, self.flour)["expiry_date"])

    def test_TS_3_5(self):
        """TS-3.5 [AC-3.3]: Verify that clearing the product name and saving is rejected, an error is shown on that field, and nothing is saved."""
        with self.assertRaises(ValidationError) as ctx:
            self.e.pm.update_product(self.e.mgr, self.rice, name="   ", threshold="9")
        self.assertIn("name", ctx.exception.errors)
        row = self.saved_row(self.rice)
        self.assertEqual((row["name"], row["low_stock_level"]), ("Rice 5kg", 5))

    def test_TS_3_6(self):
        """TS-3.6 [AC-3.3]: Verify that an invalid expiry date (for example, 31/02/2027) and a negative or non-numeric threshold are rejected, and that a threshold of 0 is accepted (boundary)."""
        with self.assertRaises(ValidationError) as ctx:
            self.e.pm.update_product(self.e.mgr, self.rice, expiry="31/02/2027")
        self.assertIn("expiry", ctx.exception.errors)
        for bad in ("-1", "abc", "2.5"):
            with self.assertRaises(ValidationError, msg=bad) as ctx:
                self.e.pm.update_product(self.e.mgr, self.rice, threshold=bad)
            self.assertIn("threshold", ctx.exception.errors)
        self.assertTrue(self.e.pm.update_product(self.e.mgr, self.rice, threshold="0"))     # boundary
        self.assertEqual(self.saved_row(self.rice)["low_stock_level"], 0)

    def test_TS_3_7(self):
        """TS-3.7 [AC-3.4]: Verify that changing a product’s name and threshold and confirming saves the change and displays a confirmation message."""
        self.assertTrue(self.e.pm.update_product(self.e.mgr, self.rice, name="Rice 10kg", threshold="8"))
        row = self.saved_row(self.rice)
        self.assertEqual((row["name"], row["low_stock_level"]), ("Rice 10kg", 8))
        # (the 'Product updated.' message itself is shown by the screen - check it by hand)

    def test_TS_3_8(self):
        """TS-3.8 [AC-3.4]: Verify that after saving, searching for the product returns the updated details, and that changing an expiry date to within 30 days makes the product appear in the nearing-expiry notification."""
        self.assertEqual(self.e.am.nearing_expiry_notifications(self.e.mgr), [])            # 40 days: not yet
        self.e.pm.update_product(self.e.mgr, self.rice, name="Rice 10kg", expiry="2026-12-10")
        listed = [r for r in self.e.pm.list_batches(self.e.mgr) if r["product_id"] == self.rice][0]
        self.assertEqual((listed["name"], listed["expiry_date"]), ("Rice 10kg", "2026-12-10"))
        notes = self.e.am.nearing_expiry_notifications(self.e.mgr)
        self.assertEqual([(n["name"], n["expiry_date"]) for n in notes], [("Rice 10kg", "2026-12-10")])

    def test_TS_3_9(self):
        """TS-3.9 [AC-3.4]: Verify that cancelling at the confirmation step, or a failed save, leaves the product unchanged and shows no success message."""
        # Cancel: the screen simply never calls update_product, so nothing changes (check by hand).
        # Failed save: force the audit-log write to fail; the whole update must roll back.
        self.e.db.conn.execute("DROP TABLE audit_log")
        with self.assertRaises(Exception):
            self.e.pm.update_product(self.e.mgr, self.rice, name="Rice 10kg", threshold="9", expiry="2026-12-10")
        row = self.saved_row(self.rice)
        self.assertEqual((row["name"], row["low_stock_level"]), ("Rice 5kg", 5))
        self.assertEqual(self.e.batch(self.rice)[0]["expiry_date"], "2027-01-02")

    def test_TS_3_10(self):
        """TS-3.10 [AC-3.5]: Verify that after a successful update the log contains the user, date and time, and the old and new values."""
        before = self.e.count("audit_log")
        self.e.pm.update_product(self.e.mgr, self.rice, name="Rice 10kg", threshold="8")
        self.assertEqual(self.e.count("audit_log"), before + 1)
        log = self.e.db.query("SELECT * FROM audit_log WHERE action = 'update_product'")[0]
        self.assertEqual(log["performed_by"], "mgr")
        self.assertTrue(log["date_time"])
        for text in ("Rice 5kg", "Rice 10kg", "5 -> 8"):
            self.assertIn(text, log["detail"])

    def test_TS_3_11(self):
        """TS-3.11 [AC-3.5]: Verify that an update rejected by validation, or cancelled by the user, creates no log entry."""
        before = self.e.count("audit_log")
        with self.assertRaises(ValidationError):
            self.e.pm.update_product(self.e.mgr, self.rice, name="")
        with self.assertRaises(DuplicateProductError):
            self.e.pm.update_product(self.e.mgr, self.rice, name="flour 1kg")      # name already used
        self.assertFalse(self.e.pm.update_product(self.e.mgr, self.rice))          # nothing changed
        self.assertEqual(self.e.count("audit_log"), before)


if __name__ == "__main__":
    unittest.main()
