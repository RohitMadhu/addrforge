import unittest

from addrforge.format import format_standardized
from addrforge.models import ParsedAddress


class FormatTests(unittest.TestCase):
    def test_street_format(self):
        address = ParsedAddress(
            raw="",
            kind="street",
            number="123",
            predir="N",
            street_name="MAIN",
            suffix="ST",
            unit_type="APT",
            unit_id="4B",
        )

        self.assertEqual(format_standardized(address), "123 N MAIN ST APT 4B")

    def test_unknown_format_is_empty_except_place_tail(self):
        address = ParsedAddress(raw="", kind="unknown", city="FAIRFAX", state="VA")

        self.assertEqual(format_standardized(address), "FAIRFAX VA")


if __name__ == "__main__":
    unittest.main()
