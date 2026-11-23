"""FID-6 Nearing-expiry notification (Tevin). One test per SRS test scenario.
Delete the @unittest.skip line as you implement each one. Pattern: tests/test_fid1_add_product.py.
Use the demo products in app/data/seed.py (add_demo_data) for test data."""
import unittest


class Fid6NearingExpiryTests(unittest.TestCase):
    @unittest.skip("TODO (Tevin)")
    def test_TS6_1A(self):
        """TS6.1A [AC6.1]: Check that at least one expiry check finishes successfully during a continuous period of 24 hours while the application is running."""
        self.fail('not written yet')

    @unittest.skip("TODO (Tevin)")
    def test_TS6_1B(self):
        """TS6.1B [AC6.1]: Check that, after more than 24 hours offline, the application completes the overdue expiry check before a sale can use old stock information."""
        self.fail('not written yet')

    @unittest.skip("TODO (Tevin)")
    def test_TS6_2A(self):
        """TS6.2A [AC6.2]: Check that eligible stock with exactly 30 days left before expiry receives a Nearing Expiry flag and remains In Stock."""
        self.fail('not written yet')

    @unittest.skip("TODO (Tevin)")
    def test_TS6_2B(self):
        """TS6.2B [AC6.2]: Check that eligible stock expiring in seven days receives a Nearing Expiry flag and remains In Stock."""
        self.fail('not written yet')

    @unittest.skip("TODO (Tevin)")
    def test_TS6_2C(self):
        """TS6.2C [AC6.2]: Check that eligible stock expiring today receives a Nearing Expiry flag under the proposed rule for expiry at the end of the day."""
        self.fail('not written yet')

    @unittest.skip("TODO (Tevin)")
    def test_TS6_2D(self):
        """TS6.2D [AC6.2]: Check that stock expiring in 31 days does not receive a Nearing Expiry flag."""
        self.fail('not written yet')

    @unittest.skip("TODO (Tevin)")
    def test_TS6_2E(self):
        """TS6.2E [AC6.2]: Check that stock which expired yesterday is shown as Expired rather than Nearing Expiry."""
        self.fail('not written yet')

    @unittest.skip("TODO (Tevin)")
    def test_TS6_3A(self):
        """TS6.3A [AC6.3]: Compare a flagged product's notification with its saved record and confirm that the name, eligible quantity and expiry date are correct."""
        self.fail('not written yet')

    @unittest.skip("TODO (Tevin)")
    def test_TS6_3B(self):
        """TS6.3B [AC6.3]: Check that notifications for several products or separate expiry groups remain clearly identifiable. A saved quantity change or expiry date correction must update the affected notification within five seconds without changing unrelated notifications."""
        self.fail('not written yet')

    @unittest.skip("TODO (Tevin)")
    def test_TS6_4A(self):
        """TS6.4A [AC6.4]: Check that stock without an expiry date produces no nearing expiry notification."""
        self.fail('not written yet')

    @unittest.skip("TODO (Tevin)")
    def test_TS6_4B(self):
        """TS6.4B [AC6.4]: Check that Damaged stock produces no nearing expiry notification, even when its expiry date is within 30 days."""
        self.fail('not written yet')

    @unittest.skip("TODO (Tevin)")
    def test_TS6_4C(self):
        """TS6.4C [AC6.4]: Check that Sold stock produces no nearing expiry notification, even when its expiry date is within 30 days."""
        self.fail('not written yet')

    @unittest.skip("TODO (Tevin)")
    def test_TS6_4D(self):
        """TS6.4D [AC6.4]: Check that Expired stock, archived products and groups with no eligible units produce no notification. When the last eligible units in a flagged group are sold or damaged, its warning must disappear while warnings for other eligible groups remain visible."""
        self.fail('not written yet')


if __name__ == "__main__":
    unittest.main()
