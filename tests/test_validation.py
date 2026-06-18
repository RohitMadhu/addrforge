import json
import unittest
from urllib.request import Request

from addrforge import CensusGeocoderProvider, NominatimProvider, validate


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return self.payload


class ValidationTests(unittest.TestCase):
    def test_census_provider_match(self):
        payload = {
            "result": {
                "addressMatches": [
                    {
                        "matchedAddress": "1600 PENNSYLVANIA AVE NW, WASHINGTON, DC, 20500",
                        "coordinates": {"x": -77.0365, "y": 38.8977},
                        "addressComponents": {"city": "WASHINGTON", "state": "DC"},
                        "tigerLine": {"side": "L"},
                    }
                ]
            }
        }

        provider = CensusGeocoderProvider(urlopen=lambda request, timeout=5.0: FakeResponse(payload))
        result = provider.validate("1600 Pennsylvania Avenue NW, Washington, DC 20500")

        self.assertTrue(result.is_valid)
        self.assertIsNone(result.is_deliverable)
        self.assertEqual(result.provider, "census")
        self.assertEqual(result.latitude, 38.8977)
        self.assertEqual(result.longitude, -77.0365)
        self.assertIn("not_delivery_validation", result.warnings)

    def test_census_provider_no_match(self):
        provider = CensusGeocoderProvider(urlopen=lambda request, timeout=5.0: FakeResponse({"result": {"addressMatches": []}}))
        result = provider.validate("123 Fakeish Madeup St, Fairfax VA 22030")

        self.assertFalse(result.is_valid)
        self.assertEqual(result.match_level, "unknown")
        self.assertIn("no_census_match", result.warnings)

    def test_nominatim_provider_match(self):
        captured = {}

        def opener(request, timeout=5.0):
            captured["request"] = request
            return FakeResponse(
                [
                    {
                        "display_name": "123 Main Street, Fairfax, Virginia, 22030, United States",
                        "lat": "38.8462",
                        "lon": "-77.3064",
                        "importance": 0.2,
                        "osm_type": "way",
                        "osm_id": 123,
                        "address": {
                            "house_number": "123",
                            "road": "Main Street",
                            "city": "Fairfax",
                            "state": "Virginia",
                            "postcode": "22030",
                            "country_code": "us",
                        },
                    }
                ]
            )

        provider = NominatimProvider(user_agent="addrforge-tests/1.0", urlopen=opener)
        result = provider.validate("123 Main Street, Fairfax VA 22030")

        self.assertTrue(result.is_valid)
        self.assertIsInstance(captured["request"], Request)
        self.assertEqual(result.latitude, 38.8462)
        self.assertEqual(result.longitude, -77.3064)
        self.assertIn("requires_osm_attribution", result.warnings)

    def test_validate_accepts_provider_object(self):
        provider = CensusGeocoderProvider(urlopen=lambda request, timeout=5.0: FakeResponse({"result": {"addressMatches": []}}))
        result = validate("123 Main St", provider=provider)

        self.assertEqual(result.provider, "census")


if __name__ == "__main__":
    unittest.main()
