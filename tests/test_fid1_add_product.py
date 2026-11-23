"""FID-1 Add Product (Jaekwon). Test names follow the SRS test scenarios (TS-1.x)."""
import unittest
from datetime import date, timedelta

from app.data.database import Database
from app.logic.errors import DuplicateProductError, PermissionDenied, ValidationError
from app.logic.login_manager import LoginManager
from app.logic.models import Role, User
from app.logic.product_manager import ProductManager

TODAY = date(2026, 11, 23)


class AddProductTests(unittest.TestCase):
    def setUp(self):
        self.db = Database()
        self.pm = ProductManager(self.db, LoginManager(self.db), today=lambda: TODAY)
        self.mgr = User(1, "mgr", Role.INVENTORY_MANAGER)

    def tearDown(self):
        self.db.close()

    def count(self):
        return self.db.query("SELECT COUNT(*) n FROM product")[0]["n"]

    def test_TS_1_1B_unauthorized_cannot_add(self):
        with self.assertRaises(PermissionDenied):
            self.pm.add_product(User(2, "c", Role.CASHIER), "Rice", 5)
        self.assertEqual(self.count(), 0)

    def test_TS_1_2B_no_expiry_allowed(self):
        self.pm.add_product(self.mgr, "Rice", 5, None)
        self.assertEqual(self.count(), 1)

    def test_TS_1_3A_empty_name_rejected(self):
        with self.assertRaises(ValidationError) as e:
            self.pm.add_product(self.mgr, "  ", 5)
        self.assertIn("name", e.exception.errors)

    def test_TS_1_3B_quantity_rules(self):
        for i, bad in enumerate(("-1", "2.5", "abc", "")):
            with self.assertRaises(ValidationError, msg=bad):
                self.pm.add_product(self.mgr, f"X{i}", bad)
        self.pm.add_product(self.mgr, "Zero", 0)             # boundary: 0 accepted
        self.assertEqual(self.count(), 1)

    def test_TS_1_3C_yesterday_rejected(self):
        with self.assertRaises(ValidationError) as e:
            self.pm.add_product(self.mgr, "Milk", 5, (TODAY - timedelta(days=1)).isoformat())
        self.assertIn("expiry", e.exception.errors)
        self.assertEqual(self.count(), 0)

    def test_TS_1_3D_today_accepted(self):
        self.pm.add_product(self.mgr, "Milk", 5, TODAY.isoformat())
        self.assertEqual(self.count(), 1)

    def test_invalid_date_and_threshold_rejected(self):
        with self.assertRaises(ValidationError) as e:
            self.pm.add_product(self.mgr, "Milk", 5, "31/02/2027", "abc")
        self.assertEqual(set(e.exception.errors), {"expiry", "threshold"})

    def test_TS_1_4A_duplicate_rejected_case_insensitive(self):
        self.pm.add_product(self.mgr, "Rice", 5)
        with self.assertRaises(DuplicateProductError):
            self.pm.add_product(self.mgr, "rice", 9)
        self.assertEqual(self.count(), 1)

    def test_TS_1_5A_saved_in_stock_with_batch_and_log(self):
        pid = self.pm.add_product(self.mgr, "Rice", 12, "2027-01-31", 4)
        b = self.db.query("SELECT * FROM stock_batch WHERE product_id=?", (pid,))[0]
        self.assertEqual((b["qty_in_stock"], b["expiry_date"]), (12, "2027-01-31"))
        self.assertEqual(len(self.db.query("SELECT * FROM audit_log")), 1)
        self.assertEqual(self.db.query("SELECT low_stock_level l FROM product")[0]["l"], 4)

    def test_atomic_failure_leaves_nothing(self):
        self.db.conn.execute("DROP TABLE audit_log")          # force a failure mid-save
        with self.assertRaises(Exception):
            self.pm.add_product(self.mgr, "Rice", 5)
        self.assertEqual(self.count(), 0)                     # product + batch rolled back


if __name__ == "__main__":
    unittest.main()
