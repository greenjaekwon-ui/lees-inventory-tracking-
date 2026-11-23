"""FID-11 Expired status (Janae). One test per SRS test scenario.
Delete the @unittest.skip line as you implement each one. Pattern: tests/test_fid1_add_product.py.
Use the demo products in app/data/seed.py (add_demo_data) for test data."""
import unittest


class Fid11ExpiredStatusTests(unittest.TestCase):
    @unittest.skip("TODO (Janae)")
    def test_TS_11_1A(self):
        """TS-11.1A [AC-11.1]: Verify that an In Stock product with an expiry date of yesterday changes to “Expired”."""
        self.fail('not written yet')

    @unittest.skip("TODO (Janae)")
    def test_TS_11_1B(self):
        """TS-11.1B [AC-11.1]: Verify that if several In Stock products are past their expiry date, all of them change to “Expired”."""
        self.fail('not written yet')

    @unittest.skip("TODO (Janae)")
    def test_TS_11_2A(self):
        """TS-11.2A [AC-11.2]: Verify that an In Stock product expiring today stays “In Stock”."""
        self.fail('not written yet')

    @unittest.skip("TODO (Janae)")
    def test_TS_11_2B(self):
        """TS-11.2B [AC-11.2]: Verify that the same product changes to “Expired” the next day."""
        self.fail('not written yet')

    @unittest.skip("TODO (Janae)")
    def test_TS_11_3A(self):
        """TS-11.3A [AC-11.3]: Verify that an In Stock product with no expiry date stays “In Stock”."""
        self.fail('not written yet')

    @unittest.skip("TODO (Janae)")
    def test_TS_11_3B(self):
        """TS-11.3B [AC-11.3]: Verify that a product with no expiry date is left alone when other products with passed dates get marked “Expired”."""
        self.fail('not written yet')

    @unittest.skip("TODO (Janae)")
    def test_TS_11_4A(self):
        """TS-11.4A [AC-11.4]: Verify that a Damaged product with a passed expiry date stays Damaged."""
        self.fail('not written yet')

    @unittest.skip("TODO (Janae)")
    def test_TS_11_4B(self):
        """TS-11.4B [AC-11.4]: Verify that a Sold product with a passed expiry date stays Sold."""
        self.fail('not written yet')


if __name__ == "__main__":
    unittest.main()
