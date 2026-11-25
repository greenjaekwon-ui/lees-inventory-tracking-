"""FID-7 Search. One test per SRS test scenario (TS-7.x)."""
import unittest
from datetime import timedelta

from app.logic.errors import PermissionDenied, ValidationError
from tests.helpers import Env

class T(unittest.TestCase):
    def setUp(self):
        self.e = Env()
        self.addCleanup(self.e.close)
        self.rice = self.e.add("Rice 5kg", 10, 3)
        self.rice_b = self.e.add("Brown Rice 1kg", 2, 3)
        self.sugar = self.e.add("Sugar 2kg", 0, 3)

    def test_TS_7_1A(self):
        """TS-7.1A [AC-7.1]: Verify that a user can perform a search using single or combined valid search parameters (name, quantity, status)."""
        names = lambda **kw: sorted(r["name"] for r in self.e.pm.search_products(self.e.cash, **kw))
        self.assertEqual(names(name="rice"), ["Brown Rice 1kg", "Rice 5kg"])
        self.assertEqual(names(min_quantity="5"), ["Rice 5kg"])
        self.assertEqual(names(name="rice", status="Low Stock"), ["Brown Rice 1kg"])
        self.assertEqual(names(max_quantity="0"), ["Sugar 2kg"])

    def test_TS_7_1B(self):
        """TS-7.1B [AC-7.1]: Verify system behavior when special characters, invalid status labels, or empty search queries are submitted."""
        with self.assertRaises(ValidationError):
            self.e.pm.search_products(self.e.mgr)                          # empty search
        with self.assertRaises(ValidationError):
            self.e.pm.search_products(self.e.mgr, status="Frozen")           # invalid status label
        with self.assertRaises(ValidationError):
            self.e.pm.search_products(self.e.mgr, min_quantity="abc")
        self.assertEqual(self.e.pm.search_products(self.e.mgr, name="'; DROP TABLE product; --"), [])
        self.assertEqual(self.e.count("product"), 3)                       # special characters are only data

    def test_TS_7_2A(self):
        """TS-7.2A [AC-7.2]: Verify that the system successfully locates an existing product record when valid matching search criteria are provided."""
        self.assertEqual(self.e.pm.search_products(self.e.mgr, name="Sugar")[0]["product_id"], self.sugar)

    def test_TS_7_2B(self):
        """TS-7.2B [AC-7.2]: Verify that the system correctly identifies when a product does not exist and displays an appropriate message."""
        self.assertEqual(self.e.pm.search_products(self.e.mgr, name="Pineapple"), [])

    def test_TS_7_3A(self):
        """TS-7.3A [AC-7.3]: Verify that search results clearly display the complete product name, current quantity, and status matching the database record."""
        row = self.e.pm.search_products(self.e.mgr, name="Rice 5kg")[0]
        self.assertEqual((row["name"], row["qty_in_stock"], row["status"]), ("Rice 5kg", 10, "In Stock"))

    def test_TS_7_3B(self):
        """TS-7.3B [AC-7.3]: Verify that when multiple products match the search criteria, all matching records are listed accurately for the user."""
        rows = self.e.pm.search_products(self.e.mgr, name="rice")
        self.assertEqual(len(rows), 2)
        self.assertEqual({r["qty_in_stock"] for r in rows}, {10, 2})

    def test_all_roles_may_search(self):
        """all roles may search"""
        for user in (self.e.mgr, self.e.owner, self.e.wh, self.e.cash):
            self.assertEqual(len(self.e.pm.search_products(user, name="rice")), 2)
        with self.assertRaises(PermissionDenied):
            self.e.pm.search_products(None, name="rice")


