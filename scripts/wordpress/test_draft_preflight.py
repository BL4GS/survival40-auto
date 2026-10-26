"""Credential-free offline tests for the draft preflight. Never contact WordPress."""
import copy
import io
import json
import unittest
import urllib.error
from unittest.mock import patch

from scripts.wordpress import draft_preflight as pf


def draft():
    return {
        "id": 620,
        "slug": "40s-male-razor-burn-shaving-care",
        "status": "draft",
        "categories": [28],
        "content": {"raw": "<p>髭剃り負けの本文</p>"},
    }


class Reply:
    status = 200

    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, size):
        return self.data


class FakeOpener:
    def __init__(self, result=None, error=None):
        self.result = result if result is not None else draft()
        self.error = error
        self.calls = 0
        self.request = None

    def open(self, request, timeout):
        self.calls += 1
        self.request = request
        if self.error is not None:
            raise self.error
        return Reply(json.dumps(self.result, ensure_ascii=False).encode("utf-8"))


class ReadOnlyPreflightTests(unittest.TestCase):
    def inspect(self, opener):
        return pf.inspect(620, pf.DEFAULT_SLUG, "wp_admin", "do-not-log-this-password", opener=opener)

    def test_authenticated_get_is_read_only_and_never_logs_body(self):
        fake = FakeOpener()
        report = self.inspect(fake)
        self.assertEqual(fake.calls, 1)
        self.assertEqual(fake.request.get_method(), "GET")
        self.assertIsNone(fake.request.data)
        self.assertIn("www.survival40.com/index.php?rest_route=", fake.request.full_url)
        self.assertNotIn("do-not-log", fake.request.full_url)
        self.assertEqual(report["post_id"], 620)
        self.assertEqual(report["categories"], [28])
        self.assertEqual(report["status"], "draft")
        self.assertEqual(report["production_writes"], 0)
        self.assertFalse(report["publication_authorized"])
        self.assertEqual(len(report["raw_content_sha256"]), 64)
        self.assertNotIn("髭剃り", json.dumps(report, ensure_ascii=False))

    def test_hash_changes_only_with_raw_body(self):
        a = draft()
        b = copy.deepcopy(a)
        b["content"]["raw"] += "差分"
        self.assertNotEqual(
            pf.draft_snapshot(a, 620, pf.DEFAULT_SLUG)["raw_content_sha256"],
            pf.draft_snapshot(b, 620, pf.DEFAULT_SLUG)["raw_content_sha256"],
        )

    def test_refuse_credentials_missing_before_network(self):
        fake = FakeOpener()
        with self.assertRaisesRegex(pf.PreflightError, "credentials missing"):
            pf.inspect(620, pf.DEFAULT_SLUG, "", "", opener=fake)
        self.assertEqual(fake.calls, 0)

    def test_refuse_unsafe_id_and_slug_before_network(self):
        for id_, slug in [(0, pf.DEFAULT_SLUG), (True, pf.DEFAULT_SLUG),
                          (620, "../wp-admin"), (620, "http://evil.test")]:
            fake = FakeOpener()
            with self.subTest(id=id_, slug=slug), self.assertRaises(pf.PreflightError):
                pf.inspect(id_, slug, "user", "password", opener=fake)
            self.assertEqual(fake.calls, 0)

    def test_refuse_any_non_draft_status(self):
        for status in ("publish", "future", "pending", "private", "trash", None):
            item = draft()
            item["status"] = status
            with self.subTest(status=status), self.assertRaisesRegex(pf.PreflightError, "not a draft"):
                self.inspect(FakeOpener(item))

    def test_refuse_mismatched_identity_and_missing_raw(self):
        cases = []
        item = draft(); item["id"] = 999; cases.append(item)
        item = draft(); item["slug"] = "other"; cases.append(item)
        item = draft(); item["content"] = {"rendered": "<p>not raw</p>"}; cases.append(item)
        item = draft(); item["content"]["raw"] = ""; cases.append(item)
        item = draft(); item["categories"] = [28, "unknown"]; cases.append(item)
        for item in cases:
            with self.subTest(item=item), self.assertRaises(pf.PreflightError):
                self.inspect(FakeOpener(item))

    def test_redirects_never_forward_authorization(self):
        with self.assertRaises(pf.PreflightError):
            pf.NoRedirects().redirect_request(None, None, 302, "moved", {}, "https://evil.test/")

    def test_http_errors_do_not_echo_private_body(self):
        error = urllib.error.HTTPError(
            "https://www.survival40.com/", 403, "private SECRET CONTENT", None,
            io.BytesIO(b"private SECRET CONTENT"),
        )
        fake = FakeOpener(error=error)
        with self.assertRaises(pf.PreflightError) as caught:
            self.inspect(fake)
        self.assertEqual(fake.calls, 1)
        self.assertIn("HTTP 403", str(caught.exception))
        self.assertNotIn("SECRET", str(caught.exception))
        self.assertNotIn("do-not-log", str(caught.exception))

    def test_refuse_oversized_result(self):
        fake = FakeOpener()
        with patch.object(pf, "MAX_RESPONSE_BYTES", 8):
            with self.assertRaisesRegex(pf.PreflightError, "size limit"):
                self.inspect(fake)

    def test_report_is_data_only_no_post_edit_method(self):
        self.assertFalse(hasattr(pf, "update_post"))
        self.assertFalse(hasattr(pf, "publish_post"))
        fake = FakeOpener()
        self.inspect(fake)
        self.assertEqual(fake.request.get_method(), "GET")


if __name__ == "__main__":
    unittest.main()
