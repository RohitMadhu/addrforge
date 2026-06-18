import io
import json
import unittest

from addrforge.cli import main


class CliTests(unittest.TestCase):
    def test_cli_standardizes_plain_text(self):
        out = io.StringIO()

        code = main(["123", "Main", "Street"], stdout=out)

        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue(), "123 MAIN ST\n")

    def test_cli_json(self):
        out = io.StringIO()

        code = main(["--json", "123", "Main", "Street"], stdout=out)

        self.assertEqual(code, 0)
        payload = json.loads(out.getvalue())
        self.assertEqual(payload["standardized"], "123 MAIN ST")

    def test_cli_lines(self):
        out = io.StringIO()

        code = main(["--lines", "123", "Main", "St", "Apt", "4B,", "Fairfax", "VA", "22030"], stdout=out)

        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue(), "123 MAIN ST\nAPT 4B\nFAIRFAX VA 22030\n")


if __name__ == "__main__":
    unittest.main()
