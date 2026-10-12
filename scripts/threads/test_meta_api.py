import json
import unittest
import urllib.error
from unittest.mock import patch
from scripts.threads.meta_api import MetaThreadsClient, ThreadsApiError


class FakeResponse:
    def __init__(self, body):
        self.body = body
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, n=-1):
        return json.dumps(self.body).encode("utf-8")


class ThreadsApiTests(unittest.TestCase):
    def setUp(self):
        self.client = MetaThreadsClient("TEST_TOKEN_NOT_REAL")

    @patch("scripts.threads.meta_api.urllib.request.urlopen")
    def test_identity_matches(self, urlopen):
        urlopen.return_value = FakeResponse({"id": "12345", "username": "survival40_jp"})
        self.assertEqual(self.client.verify_account("12345")["username"], "survival40_jp")
        req = urlopen.call_args.args[0]
        self.assertIn("/me?", req.full_url)
        self.assertEqual(req.get_header("Authorization"), "Bearer TEST_TOKEN_NOT_REAL")

    @patch("scripts.threads.meta_api.urllib.request.urlopen")
    def test_wrong_account_fails_closed(self, urlopen):
        urlopen.return_value = FakeResponse({"id": "222", "username": "some_person"})
        with self.assertRaises(ThreadsApiError):
            self.client.verify_account("123")

    @patch("scripts.threads.meta_api.urllib.request.urlopen")
    def test_container_is_not_auto_published(self, urlopen):
        urlopen.return_value = FakeResponse({"id": "123456"})
        self.assertEqual(self.client.create_text_container("おはようございます！"), "123456")
        req = urlopen.call_args.args[0]
        self.assertEqual(req.get_method(), "POST")
        self.assertIn(b"auto_publish_text=false", req.data)
        self.assertIn(b"media_type=TEXT", req.data)
        self.assertEqual(req.full_url, "https://graph.threads.net/me/threads")

    @patch("scripts.threads.meta_api.urllib.request.urlopen")
    def test_publish_requires_numeric_id(self, urlopen):
        with self.assertRaises(ValueError):
            self.client.publish_container("invalid")
        urlopen.assert_not_called()

    @patch("scripts.threads.meta_api.urllib.request.urlopen")
    def test_publish_response_requires_post_id(self, urlopen):
        urlopen.return_value = FakeResponse({"success": True})
        with self.assertRaises(ThreadsApiError):
            self.client.publish_container("12345")

    @patch("scripts.threads.meta_api.urllib.request.urlopen")
    def test_error_does_not_leak_token(self, urlopen):
        urlopen.side_effect = urllib.error.HTTPError("https://graph.threads.net/me", 403, "Forbidden", {}, None)
        with self.assertRaises(ThreadsApiError) as caught:
            self.client.verify_account("123")
        self.assertNotIn("TEST_TOKEN_NOT_REAL", str(caught.exception))

    def test_no_token(self):
        with self.assertRaises(ValueError):
            MetaThreadsClient("")


if __name__ == "__main__":
    unittest.main()
