import json
import pathlib
import unittest

from addrforge import parse


class FixtureCorpusTests(unittest.TestCase):
    def test_address_fixture_corpus(self):
        fixture_path = pathlib.Path(__file__).parent / "fixtures" / "addresses.json"
        cases = json.loads(fixture_path.read_text())

        for case in cases:
            with self.subTest(address=case["input"]):
                parsed = parse(case["input"])
                self.assertEqual(parsed.kind, case["kind"])
                self.assertEqual(parsed.standardized, case["standardized"])
                if "complete" in case:
                    self.assertEqual(parsed.is_complete_for_mailing, case["complete"])
                if "is_us" in case:
                    self.assertEqual(parsed.is_us, case["is_us"])


if __name__ == "__main__":
    unittest.main()
