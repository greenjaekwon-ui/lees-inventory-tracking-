"""LoginManager (SEC-1/2/3) and BusinessRules boundaries (QA-3). Everyone can reuse these dates."""
import unittest
from datetime import date, timedelta

from app.data.database import Database
from app.data.seed import add_demo_data, ensure_seed
from app.logic.errors import AuthError, PermissionDenied
from app.logic.login_manager import LoginManager
from app.logic.rules import BusinessRules as R

TODAY = date(2026, 11, 23)


class LoginTests(unittest.TestCase):
    def setUp(self):
        self.db = Database()
        self.addCleanup(self.db.close)
        ensure_seed(self.db)
        self.login = LoginManager(self.db)

    def test_good_login_returns_user_with_role(self):
        u = self.login.authenticate("manager", "manager123")
        self.assertEqual(u.username, "manager")
        self.assertTrue(u.has_permission("add_product"))

    def test_wrong_user_and_wrong_password_give_the_same_message(self):
        with self.assertRaises(AuthError) as a:
            self.login.authenticate("nobody", "x")
        with self.assertRaises(AuthError) as b:
            self.login.authenticate("manager", "wrong")
        self.assertEqual(str(a.exception), str(b.exception))

    def test_password_is_not_stored_in_plain_text(self):
        stored = self.db.query("SELECT password_hash FROM user WHERE username='manager'")[0][0]
        self.assertNotIn("manager123", stored)

    def test_cashier_cannot_add_or_record_damage(self):
        c = self.login.authenticate("cashier", "cashier123")
        for action in ("add_product", "record_damage"):
            with self.assertRaises(PermissionDenied):
                self.login.require(c, action)


class RulesTests(unittest.TestCase):
    def d(self, days):
        return TODAY + timedelta(days=days)

    def test_nearing_expiry_window_is_0_to_30_days(self):
        self.assertTrue(R.is_nearing_expiry(self.d(0), TODAY))
        self.assertTrue(R.is_nearing_expiry(self.d(30), TODAY))
        self.assertFalse(R.is_nearing_expiry(self.d(31), TODAY))
        self.assertFalse(R.is_nearing_expiry(self.d(-1), TODAY))
        self.assertFalse(R.is_nearing_expiry(None, TODAY))

    def test_expired_only_the_day_after(self):
        self.assertFalse(R.is_past_expiry(self.d(0), TODAY))
        self.assertTrue(R.is_past_expiry(self.d(-1), TODAY))

    def test_low_stock_is_equal_or_below(self):
        self.assertTrue(R.is_low_stock(5, 5))
        self.assertTrue(R.is_low_stock(4, 5))
        self.assertFalse(R.is_low_stock(6, 5))

    def test_can_sell(self):
        self.assertTrue(R.can_sell(10, 3, self.d(5), TODAY))
        self.assertFalse(R.can_sell(10, 11, None, TODAY))
        self.assertFalse(R.can_sell(10, 3, self.d(-1), TODAY))


class DemoDataTests(unittest.TestCase):
    def test_demo_data_loads_once(self):
        db = Database()
        self.addCleanup(db.close)
        add_demo_data(db, TODAY)
        add_demo_data(db, TODAY)           # second call must not duplicate
        self.assertEqual(db.query("SELECT COUNT(*) FROM product")[0][0], 8)


if __name__ == "__main__":
    unittest.main()
