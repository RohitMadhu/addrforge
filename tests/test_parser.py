import unittest
import json

from addrforge import is_probably_address, parse, standardize


class ParserTests(unittest.TestCase):
    def test_street_with_unit(self):
        parsed = parse("123 north main street apartment 4b")

        self.assertEqual(parsed.kind, "street")
        self.assertEqual(parsed.number, "123")
        self.assertEqual(parsed.predir, "N")
        self.assertEqual(parsed.street_name, "MAIN")
        self.assertEqual(parsed.suffix, "ST")
        self.assertEqual(parsed.unit_type, "APT")
        self.assertEqual(parsed.unit_id, "4B")
        self.assertEqual(parsed.standardized, "123 N MAIN ST APT 4B")
        self.assertGreaterEqual(parsed.confidence, 0.9)
        self.assertEqual(parsed.parse_notes, ("missing_place_tail",))

    def test_street_with_hash_unit(self):
        parsed = parse("123 Main Street #200")

        self.assertEqual(parsed.kind, "street")
        self.assertEqual(parsed.unit_type, "UNIT")
        self.assertEqual(parsed.unit_id, "200")
        self.assertEqual(parsed.standardized, "123 MAIN ST UNIT 200")

    def test_street_with_number_unit_designator(self):
        parsed = parse("123 Main Street No. 4")

        self.assertEqual(parsed.kind, "street")
        self.assertEqual(parsed.unit_type, "UNIT")
        self.assertEqual(parsed.unit_id, "4")
        self.assertEqual(parsed.standardized, "123 MAIN ST UNIT 4")

    def test_unit_before_street(self):
        parsed = parse("Suite 200 123 Main Street")

        self.assertEqual(parsed.kind, "street")
        self.assertEqual(parsed.number, "123")
        self.assertEqual(parsed.unit_type, "STE")
        self.assertEqual(parsed.unit_id, "200")
        self.assertEqual(parsed.standardized, "123 MAIN ST STE 200")

    def test_street_with_city_state_zip(self):
        parsed = parse("1600 Pennsylvania Avenue NW, Washington, DC 20500")

        self.assertEqual(parsed.kind, "street")
        self.assertEqual(parsed.number, "1600")
        self.assertEqual(parsed.street_name, "PENNSYLVANIA")
        self.assertEqual(parsed.suffix, "AVE")
        self.assertEqual(parsed.postdir, "NW")
        self.assertEqual(parsed.city, "WASHINGTON")
        self.assertEqual(parsed.state, "DC")
        self.assertEqual(parsed.zip_code, "20500")
        self.assertEqual(parsed.standardized, "1600 PENNSYLVANIA AVE NW WASHINGTON DC 20500")
        self.assertTrue(parsed.is_complete_for_mailing)
        self.assertEqual(parsed.match_level, "exact-ish")
        self.assertEqual(parsed.components_missing, ())

    def test_street_without_number(self):
        parsed = parse("42nd Street")

        self.assertEqual(parsed.kind, "street")
        self.assertIsNone(parsed.number)
        self.assertEqual(parsed.street_name, "42ND")
        self.assertEqual(parsed.suffix, "ST")

    def test_hyphenated_house_number(self):
        self.assertEqual(standardize("12-14 W Elm Rd"), "12-14 W ELM RD")

    def test_unknown_non_address(self):
        parsed = parse("hello world")

        self.assertEqual(parsed.kind, "unknown")
        self.assertEqual(parsed.standardized, "")
        self.assertFalse(is_probably_address("hello world"))

    def test_partial_parse_keeps_raw(self):
        parsed = parse("Main Street")

        self.assertEqual(parsed.kind, "street")
        self.assertEqual(parsed.raw, "Main Street")
        self.assertEqual(parsed.standardized, "MAIN ST")
        self.assertLess(parsed.confidence, 0.9)
        self.assertIn("missing_house_number", parsed.parse_notes)
        self.assertEqual(parsed.match_level, "partial")
        self.assertFalse(parsed.is_complete_for_mailing)

    def test_strict_mode_rejects_incomplete_partial_parse(self):
        parsed = parse("Main Street", strict=True)

        self.assertEqual(parsed.kind, "unknown")
        self.assertEqual(parsed.standardized, "")
        self.assertEqual(parsed.reject_reason, "strict_incomplete_address")
        self.assertIn("strict_incomplete_address", parsed.warnings)

    def test_to_dict_and_to_json(self):
        parsed = parse("123 Main Street, Fairfax VA 22030")

        self.assertEqual(parsed.to_dict()["standardized"], "123 MAIN ST FAIRFAX VA 22030")
        self.assertEqual(json.loads(parsed.to_json())["kind"], "street")

    def test_non_us_address_is_rejected_cleanly(self):
        parsed = parse("123 Main St, Toronto ON M5V 2T6 Canada")

        self.assertEqual(parsed.kind, "unknown")
        self.assertFalse(parsed.is_us)
        self.assertEqual(parsed.reject_reason, "non_us_country")
        self.assertIn("non_us_address", parsed.parse_notes)

    def test_publication_28_style_suffixes(self):
        cases = {
            "123 Ocean Causeway": "123 OCEAN CSWY",
            "456 Cedar Crescent": "456 CEDAR CRES",
            "789 Lake Viaduct": "789 LAKE VIA",
            "321 Pine Junction": "321 PINE JCT",
        }

        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(standardize(raw), expected)


class RouteTests(unittest.TestCase):
    def test_us_route_with_city_state(self):
        parsed = parse("US 29 Fairfax VA")

        self.assertEqual(parsed.kind, "route")
        self.assertEqual(parsed.route, "US 29")
        self.assertEqual(parsed.city, "FAIRFAX")
        self.assertEqual(parsed.state, "VA")
        self.assertGreaterEqual(parsed.confidence, 0.9)

    def test_county_road(self):
        parsed = parse("County Road 12")

        self.assertEqual(parsed.kind, "route")
        self.assertEqual(parsed.standardized, "COUNTY ROAD 12")

    def test_interstate(self):
        self.assertEqual(parse("I-95").kind, "route")


class PoBoxTests(unittest.TestCase):
    def test_po_box_city_state_zip(self):
        parsed = parse("PO Box 45, Fairfax, VA 22030")

        self.assertEqual(parsed.kind, "po_box")
        self.assertEqual(parsed.po_box, "45")
        self.assertEqual(parsed.city, "FAIRFAX")
        self.assertEqual(parsed.state, "VA")
        self.assertEqual(parsed.zip_code, "22030")
        self.assertEqual(parsed.standardized, "PO BOX 45 FAIRFAX VA 22030")

    def test_post_office_box(self):
        self.assertEqual(standardize("Post Office Box 9"), "PO BOX 9")

    def test_rural_route_box(self):
        parsed = parse("Rural Route 2 Box 152, Fairfax VA 22030")

        self.assertEqual(parsed.kind, "po_box")
        self.assertEqual(parsed.po_box, "RR 2 BOX 152")
        self.assertEqual(parsed.standardized, "RR 2 BOX 152 FAIRFAX VA 22030")

    def test_highway_contract_box(self):
        self.assertEqual(standardize("HC 67 Box 12, Austin TX 78701"), "HC 67 BOX 12 AUSTIN TX 78701")

    def test_military_psc_box(self):
        parsed = parse("PSC 123 Box 456 APO AE 09012")

        self.assertEqual(parsed.kind, "po_box")
        self.assertEqual(parsed.city, "APO")
        self.assertEqual(parsed.state, "AE")
        self.assertEqual(parsed.zip_code, "09012")
        self.assertEqual(parsed.standardized, "PSC 123 BOX 456 APO AE 09012")


if __name__ == "__main__":
    unittest.main()
