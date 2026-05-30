import unittest

from addrforge.normalize import (
    normalize_directional,
    normalize_suffix,
    normalize_unit_type,
    preprocess,
)


class NormalizeTests(unittest.TestCase):
    def test_directionals(self):
        self.assertEqual(normalize_directional("North"), "N")
        self.assertEqual(normalize_directional("southwest"), "SW")

    def test_unit_types(self):
        self.assertEqual(normalize_unit_type("Apartment"), "APT")
        self.assertEqual(normalize_unit_type("Suite"), "STE")
        self.assertEqual(normalize_unit_type("Floor"), "FL")
        self.assertEqual(normalize_unit_type("Building"), "BLDG")
        self.assertEqual(normalize_unit_type("No"), "UNIT")
        self.assertEqual(normalize_unit_type("Penthouse"), "PH")

    def test_suffixes(self):
        self.assertEqual(normalize_suffix("Street"), "ST")
        self.assertEqual(normalize_suffix("Avenue"), "AVE")
        self.assertEqual(normalize_suffix("Road"), "RD")
        self.assertEqual(normalize_suffix("Causeway"), "CSWY")
        self.assertEqual(normalize_suffix("Viaduct"), "VIA")

    def test_preprocess_preserves_meaningful_hyphens(self):
        self.assertEqual(preprocess("  P.O. Box 45,  Fairfax, VA 22030-1234 "), "PO Box 45, Fairfax, VA 22030-1234")


if __name__ == "__main__":
    unittest.main()
