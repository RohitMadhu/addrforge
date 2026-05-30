import unittest

from addrforge import split_lines


class LineSplitTests(unittest.TestCase):
    def test_split_street_unit_and_place_tail(self):
        lines = split_lines("123 Main St Apt 4B, Fairfax VA 22030")

        self.assertEqual(lines.line1, "123 MAIN ST")
        self.assertEqual(lines.line2, "APT 4B")
        self.assertEqual(lines.city, "FAIRFAX")
        self.assertEqual(lines.state, "VA")
        self.assertEqual(lines.zip_code, "22030")
        self.assertEqual(lines.standardized, "123 MAIN ST APT 4B FAIRFAX VA 22030")

    def test_split_po_box(self):
        lines = split_lines("PO Box 45, Fairfax, VA 22030")

        self.assertEqual(lines.line1, "PO BOX 45")
        self.assertEqual(lines.line2, "")


if __name__ == "__main__":
    unittest.main()
