"""Checks which endpoint google_cse_client calls. No network: requests.get is mocked.

Run from this folder:  python -m unittest test_google_cse_client
"""

import configparser
import unittest
from unittest import mock

import google_cse_client
from google_cse_client import CSE_URL, GoogleCSEError, google_cse_search


def _config(**extra) -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    cfg["google_cse"] = {"api_key": "test-key", "cx": "test-cx", **extra}
    return cfg


def _response(items):
    r = mock.Mock()
    r.status_code = 200
    r.json.return_value = {"items": items}
    return r


ITEM = {"title": "t", "snippet": "s", "link": "https://example.com/a"}


@mock.patch.object(google_cse_client, "_enrich_records", lambda records: None)
class EndpointTest(unittest.TestCase):
    def test_default_is_google(self):
        with mock.patch.object(google_cse_client.requests, "get", return_value=_response([ITEM])) as get:
            records, _ = google_cse_search("osint", count=1, config=_config())
        self.assertEqual(get.call_args.args[0], "https://www.googleapis.com/customsearch/v1")
        self.assertEqual(get.call_args.args[0], CSE_URL)
        self.assertEqual(records[0]["result_url"], "https://example.com/a")

    def test_empty_base_url_is_google(self):
        with mock.patch.object(google_cse_client.requests, "get", return_value=_response([ITEM])) as get:
            google_cse_search("osint", count=1, config=_config(base_url=""))
        self.assertEqual(get.call_args.args[0], CSE_URL)

    def test_base_url_override(self):
        url = "http://127.0.0.1:8080/customsearch/v1"
        with mock.patch.object(google_cse_client.requests, "get", return_value=_response([ITEM])) as get:
            google_cse_search("osint", count=1, config=_config(base_url=url))
        self.assertEqual(get.call_args.args[0], url)
        self.assertEqual(get.call_args.kwargs["params"]["cx"], "test-cx")
        self.assertEqual(get.call_args.kwargs["params"]["q"], "osint")

    def test_base_url_must_be_http(self):
        with mock.patch.object(google_cse_client.requests, "get") as get:
            with self.assertRaises(GoogleCSEError):
                google_cse_search("osint", config=_config(base_url="file:///etc/passwd"))
        get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
