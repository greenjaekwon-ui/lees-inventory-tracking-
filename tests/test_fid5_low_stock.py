"""FID-5 Low-stock alert (Ricardo). One test per SRS test scenario.
Delete the @unittest.skip line as you implement each one. Pattern: tests/test_fid1_add_product.py.
Use the demo products in app/data/seed.py (add_demo_data) for test data."""
import unittest


class Fid5LowStockTests(unittest.TestCase):
    @unittest.skip("TODO (Ricardo)")
    def test_TS_5_1A(self):
        """TS-5.1A [AC-5.1]: Verify that a user enters correct data in credential fields."""
        self.fail('not written yet')

    @unittest.skip("TODO (Ricardo)")
    def test_TS_5_1B(self):
        """TS-5.1B [AC-5.1]: When user enters invalid or incomplete credentials, an error is displayed"""
        self.fail('not written yet')

    @unittest.skip("TODO (Ricardo)")
    def test_TS_5_2A(self):
        """TS-5.2A [AC-5.2]: Verify that the product listing match item alert"""
        self.fail('not written yet')

    @unittest.skip("TODO (Ricardo)")
    def test_TS_5_2B(self):
        """TS-5.2B [AC-5.2]: Verify that a “Unknown Product” is listed when the product does not exist"""
        self.fail('not written yet')

    @unittest.skip("TODO (Ricardo)")
    def test_TS_5_3A(self):
        """TS-5.3A [AC-5.3]: Verify that accurate quantity is displayed"""
        self.fail('not written yet')

    @unittest.skip("TODO (Ricardo)")
    def test_TS_5_3B(self):
        """TS-5.3B [AC-5.3]: When inaccurate quantity displayed, an error is displayed"""
        self.fail('not written yet')

    @unittest.skip("TODO (Ricardo)")
    def test_TS_5_4A(self):
        """TS-5.4A [AC-5.4]: Verify that low-stock alerts are displayed when stock quantities meet or are below threshold"""
        self.fail('not written yet')

    @unittest.skip("TODO (Ricardo)")
    def test_TS_5_4B(self):
        """TS-5.4B [AC-5.4]: Verify normal behaviour if quantities are above threshold"""
        self.fail('not written yet')


if __name__ == "__main__":
    unittest.main()
