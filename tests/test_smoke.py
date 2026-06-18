import unittest

import addrforge


class SmokeTests(unittest.TestCase):
    def test_public_api(self):
        self.assertTrue(hasattr(addrforge, "parse"))
        self.assertTrue(hasattr(addrforge, "standardize"))
        self.assertTrue(hasattr(addrforge, "is_probably_address"))
        self.assertTrue(hasattr(addrforge, "ParsedAddress"))
        self.assertTrue(hasattr(addrforge, "explain"))

    def test_standardize_smoke(self):
        self.assertEqual(addrforge.standardize("Ste 200 123 Main Street"), "123 MAIN ST STE 200")
        self.assertEqual(addrforge.standardize("123 Main Street Ste 200"), "123 MAIN ST STE 200")
        self.assertEqual(addrforge.standardize("P.O. Box 45"), "PO BOX 45")

    def test_explain_smoke(self):
        self.assertIn("missing_house_number", addrforge.explain("Main Street"))


if __name__ == "__main__":
    unittest.main()
