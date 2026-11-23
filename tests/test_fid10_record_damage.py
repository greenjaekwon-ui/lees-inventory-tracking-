"""FID-10 Record damaged product (D'mitri). One test per SRS test scenario.
Delete the @unittest.skip line as you implement each one. Pattern: tests/test_fid1_add_product.py.
Use the demo products in app/data/seed.py (add_demo_data) for test data."""
import unittest


class Fid10RecordDamageTests(unittest.TestCase):
    @unittest.skip("TODO (D'mitri)")
    def test_TS_10_1A(self):
        """TS-10.1A [AC-10.1]: Verify that a logged-in Warehouse/Stock Staff user and a logged-in Stock/Inventory Manager user can open the Record Damaged Product form."""
        self.fail('not written yet')

    @unittest.skip("TODO (D'mitri)")
    def test_TS_10_1B(self):
        """TS-10.1B [AC-10.1]: Verify that a Sales/Cashier user, and a user who is not logged in, cannot access the form and receive an access denied message."""
        self.fail('not written yet')

    @unittest.skip("TODO (D'mitri)")
    def test_TS_10_2A(self):
        """TS-10.2A [AC-10.2]: Verify that a user can select an existing product and enter a damaged quantity, a reason and a note, and that the values are retained until submission."""
        self.fail('not written yet')

    @unittest.skip("TODO (D'mitri)")
    def test_TS_10_2B(self):
        """TS-10.2B [AC-10.2]: Verify that an entry with the note left blank can be submitted."""
        self.fail('not written yet')

    @unittest.skip("TODO (D'mitri)")
    def test_TS_10_3A(self):
        """TS-10.3A [AC-10.3]: Verify that an entry with no product selected, or no reason selected, is rejected and an error is displayed on each missing field."""
        self.fail('not written yet')

    @unittest.skip("TODO (D'mitri)")
    def test_TS_10_3B(self):
        """TS-10.3B [AC-10.3]: Verify that a damaged quantity that is negative, decimal, non-numeric or 0 is rejected, and that a quantity of 1 is accepted (boundary)."""
        self.fail('not written yet')

    @unittest.skip("TODO (D'mitri)")
    def test_TS_10_3C(self):
        """TS-10.3C [AC-10.3]: Verify that a damaged quantity greater than the product’s current quantity is rejected, and that a damaged quantity equal to the current quantity is accepted (boundary)."""
        self.fail('not written yet')

    @unittest.skip("TODO (D'mitri)")
    def test_TS_10_3D(self):
        """TS-10.3D [AC-10.3]: Verify that an entry for a product with the status Sold, Damaged or Expired is rejected with an error message."""
        self.fail('not written yet')

    @unittest.skip("TODO (D'mitri)")
    def test_TS_10_3E(self):
        """TS-10.3E [AC-10.3]: Verify that a note of exactly 200 characters is accepted and a note of 201 characters is rejected (boundary)."""
        self.fail('not written yet')

    @unittest.skip("TODO (D'mitri)")
    def test_TS_10_4A(self):
        """TS-10.4A [AC-10.4]: Verify that recording 3 damaged units for a product with a quantity of 10 changes its quantity to 7."""
        self.fail('not written yet')

    @unittest.skip("TODO (D'mitri)")
    def test_TS_10_4B(self):
        """TS-10.4B [AC-10.4]: Verify that a rejected entry leaves the product’s quantity unchanged."""
        self.fail('not written yet')

    @unittest.skip("TODO (D'mitri)")
    def test_TS_10_4C(self):
        """TS-10.4C [AC-10.4]: Verify that searching for the product within 2 seconds of saving shows the reduced quantity."""
        self.fail('not written yet')

    @unittest.skip("TODO (D'mitri)")
    def test_TS_10_5A(self):
        """TS-10.5A [AC-10.5]: Verify that recording damage for all 4 units of a product with a quantity of 4 sets its status to Damaged and its quantity to 0."""
        self.fail('not written yet')

    @unittest.skip("TODO (D'mitri)")
    def test_TS_10_5B(self):
        """TS-10.5B [AC-10.5]: Verify that recording 1 damaged unit for a product with a quantity of 4 leaves its status as In Stock with a quantity of 3."""
        self.fail('not written yet')

    @unittest.skip("TODO (D'mitri)")
    def test_TS_10_6A(self):
        """TS-10.6A [AC-10.6]: Verify that a valid entry creates exactly one damage record containing the product name, quantity, reason, note, date and time, and username."""
        self.fail('not written yet')

    @unittest.skip("TODO (D'mitri)")
    def test_TS_10_6B(self):
        """TS-10.6B [AC-10.6]: Verify that a rejected entry creates no damage record."""
        self.fail('not written yet')

    @unittest.skip("TODO (D'mitri)")
    def test_TS_10_7A(self):
        """TS-10.7A [AC-10.7]: Verify that after a successful save a confirmation message shows the product name, damaged quantity and remaining quantity."""
        self.fail('not written yet')

    @unittest.skip("TODO (D'mitri)")
    def test_TS_10_7B(self):
        """TS-10.7B [AC-10.7]: Verify that when the save fails (for example, the database is unavailable) an error message is shown, the quantity, status and damage records are unchanged, and the entered data remains on the form."""
        self.fail('not written yet')


if __name__ == "__main__":
    unittest.main()
