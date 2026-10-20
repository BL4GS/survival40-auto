"""Offline tests for one bounded 503 retry in advisory-only Gemini generation."""
import importlib.util
import io
from pathlib import Path
import urllib.error
import unittest
from unittest.mock import Mock

SOURCE = Path(__file__).with_name("nightly_review.py")
spec = importlib.util.spec_from_file_location("nightly_review_under_test", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def error(code):
    # The body deliberately contains a sensitive-looking value: never printed.
    return urllib.error.HTTPError(
        "https://generativelanguage.googleapis.com/strict-test",
        code, "test", {}, io.BytesIO(b"do-not-expose-secret-payload"),
    )


class AdvisoryRetryTests(unittest.TestCase):
    def setUp(self):
        self.request = object()
        self.response = b'{"candidates":[]}'
        self.pause = Mock()

    def test_success_never_retries_or_waits(self):
        opener = Mock(return_value=io.BytesIO(self.response))
        actual = module.request_bounded_advisory(
            self.request, opener=opener, wait=self.pause)
        self.assertEqual(actual, {"candidates": []})
        opener.assert_called_once_with(self.request, timeout=90)
        self.pause.assert_not_called()

    def test_transient_503_uses_exactly_one_retry(self):
        opener = Mock(side_effect=[error(503), io.BytesIO(self.response)])
        actual = module.request_bounded_advisory(
            self.request, opener=opener, wait=self.pause)
        self.assertEqual(actual, {"candidates": []})
        self.assertEqual(opener.call_count, 2)
        self.pause.assert_called_once_with(2)

    def test_repeated_503_fails_closed_and_does_not_leak_body(self):
        opener = Mock(side_effect=[error(503), error(503)])
        with self.assertRaises(SystemExit) as raised:
            module.request_bounded_advisory(
                self.request, opener=opener, wait=self.pause)
        self.assertIn("HTTP 503", str(raised.exception))
        self.assertIn("withheld", str(raised.exception))
        self.assertNotIn("do-not-expose", str(raised.exception))
        self.assertEqual(opener.call_count, 2)
        self.pause.assert_called_once_with(2)

    def test_429_and_auth_errors_are_never_retried(self):
        for status in (400, 401, 403, 429, 500):
            with self.subTest(status=status):
                opener = Mock(side_effect=error(status))
                waiting = Mock()
                with self.assertRaises(SystemExit) as raised:
                    module.request_bounded_advisory(
                        self.request, opener=opener, wait=waiting)
                self.assertIn(f"HTTP {status}", str(raised.exception))
                opener.assert_called_once()
                waiting.assert_not_called()

    def test_unknown_network_and_timeout_not_retried(self):
        for ex in (urllib.error.URLError("network"), TimeoutError()):
            with self.subTest(ex=type(ex).__name__):
                opener, waiting = Mock(side_effect=ex), Mock()
                with self.assertRaises(SystemExit):
                    module.request_bounded_advisory(
                        self.request, opener=opener, wait=waiting)
                opener.assert_called_once()
                waiting.assert_not_called()

    def test_unexpected_non_json_envelope_is_not_silently_accepted(self):
        opener = Mock(return_value=io.BytesIO(b"invalid json"))
        with self.assertRaises(ValueError):
            module.request_bounded_advisory(
                self.request, opener=opener, wait=self.pause)
        opener.assert_called_once()
        self.pause.assert_not_called()


if __name__ == "__main__":
    unittest.main()
