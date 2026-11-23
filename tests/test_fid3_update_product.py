"""FID-3 Update Product (Brandon). One test per SRS test scenario.
Delete the @unittest.skip line as you implement each one. Pattern: tests/test_fid1_add_product.py.
Use the demo products in app/data/seed.py (add_demo_data) for test data."""
import unittest


class Fid3UpdateProductTests(unittest.TestCase):
    @unittest.skip("TODO (Brandon)")
    def test_TS_3_1(self):
        """TS-3.1 [AC-3.1]: Verify that an authorized user can open the update screen for a product."""
        self.fail('not written yet')

    @unittest.skip("TODO (Brandon)")
    def test_TS_3_2(self):
        """TS-3.2 [AC-3.1]: Verify that a user without authorization, or a user who is not signed in, cannot access the update screen and receives an access denied message."""
        self.fail('not written yet')

    @unittest.skip("TODO (Brandon)")
    def test_TS_3_3(self):
        """TS-3.3 [AC-3.2]: Verify that the details shown for a selected product match its saved record."""
        self.fail('not written yet')

    @unittest.skip("TODO (Brandon)")
    def test_TS_3_4(self):
        """TS-3.4 [AC-3.2]: Verify that a product with no expiry date displays a blank expiry field, with no error or incorrect date."""
        self.fail('not written yet')

    @unittest.skip("TODO (Brandon)")
    def test_TS_3_5(self):
        """TS-3.5 [AC-3.3]: Verify that clearing the product name and saving is rejected, an error is shown on that field, and nothing is saved."""
        self.fail('not written yet')

    @unittest.skip("TODO (Brandon)")
    def test_TS_3_6(self):
        """TS-3.6 [AC-3.3]: Verify that an invalid expiry date (for example, 31/02/2027) and a negative or non-numeric threshold are rejected, and that a threshold of 0 is accepted (boundary)."""
        self.fail('not written yet')

    @unittest.skip("TODO (Brandon)")
    def test_TS_3_7(self):
        """TS-3.7 [AC-3.4]: Verify that changing a product’s name and threshold and confirming saves the change and displays a confirmation message."""
        self.fail('not written yet')

    @unittest.skip("TODO (Brandon)")
    def test_TS_3_8(self):
        """TS-3.8 [AC-3.4]: Verify that after saving, searching for the product returns the updated details, and that changing an expiry date to within 30 days makes the product appear in the nearing-expiry notification."""
        self.fail('not written yet')

    @unittest.skip("TODO (Brandon)")
    def test_TS_3_9(self):
        """TS-3.9 [AC-3.4]: Verify that cancelling at the confirmation step, or a failed save, leaves the product unchanged and shows no success message."""
        self.fail('not written yet')

    @unittest.skip("TODO (Brandon)")
    def test_TS_3_10(self):
        """TS-3.10 [AC-3.5]: Verify that after a successful update the log contains the user, date and time, and the old and new values."""
        self.fail('not written yet')

    @unittest.skip("TODO (Brandon)")
    def test_TS_3_11(self):
        """TS-3.11 [AC-3.5]: Verify that an update rejected by validation, or cancelled by the user, creates no log entry."""
        self.fail('not written yet')


if __name__ == "__main__":
    unittest.main()
