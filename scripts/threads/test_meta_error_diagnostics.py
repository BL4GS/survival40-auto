"""Offline-only error triage: never send Meta requests, replay posts or expose secrets."""
import io
import json
import unittest
import urllib.error
from unittest.mock import patch

from scripts.threads.meta_api import MetaThreadsClient, ThreadsApiError


class MetaErrorDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.client = MetaThreadsClient("PRIVATE_SAMPLE_TOKEN_SHOULD_NEVER_LEAK")

    def fail_response(self, stage, error):
        data=json.dumps({"error":error},ensure_ascii=False).encode("utf-8")
        return urllib.error.HTTPError(
            "https://graph.threads.net" + stage,400,"Bad Request",{},io.BytesIO(data)
        )

    @patch("scripts.threads.meta_api.urllib.request.urlopen")
    def test_container_error_stage_and_safe_codes(self, send):
        send.side_effect=self.fail_response("/me/threads",{
            "code":24,"error_subcode":4279009,"is_transient":False,
            "message":"This response includes PRIVATE_SAMPLE_TOKEN_SHOULD_NEVER_LEAK and a user name",
            "fbtrace_id":"SECRET_INTERNAL_TRACE"
        })
        with self.assertRaises(ThreadsApiError) as ctx:
            self.client.create_text_container("日焼け止めの記事を紹介します。")
        msg=str(ctx.exception)
        self.assertIn("HTTP 400 at create_text_container",msg)
        self.assertIn("code=24",msg)
        self.assertIn("error_subcode=4279009",msg)
        self.assertIn("transient=false",msg)
        self.assertNotIn("PRIVATE_SAMPLE_TOKEN_SHOULD_NEVER_LEAK",msg)
        self.assertNotIn("user name",msg)
        self.assertNotIn("fbtrace_id",msg)
        self.assertEqual(send.call_count,1)

    @patch("scripts.threads.meta_api.urllib.request.urlopen")
    def test_publish_error_is_distinct_from_container(self, send):
        send.side_effect=self.fail_response("/me/threads_publish",{
            "code":100,"error_subcode":33,"is_transient":True})
        with self.assertRaises(ThreadsApiError) as ctx:
            self.client.publish_container("12345678")
        self.assertIn("at publish_container",str(ctx.exception))
        self.assertIn("error_subcode=33",str(ctx.exception))
        self.assertIn("transient=true",str(ctx.exception))
        self.assertEqual(send.call_count,1)

    @patch("scripts.threads.meta_api.urllib.request.urlopen")
    def test_missing_malformed_or_non_numeric_fields_fail_closed(self, send):
        for payload in (
            b"not JSON",
            b'{"error":{"code":"12345","error_subcode":"PASSWORD","is_transient":"true"}}',
            b'{"error":{"code":-1,"error_subcode":1000000000}}',
        ):
            with self.subTest(payload=payload):
                send.side_effect=urllib.error.HTTPError(
                    "https://graph.threads.net/me/threads",400,"Bad Request",{},io.BytesIO(payload))
                with self.assertRaises(ThreadsApiError) as ctx:
                    self.client.create_text_container("正常なテキスト")
                self.assertEqual(str(ctx.exception),
                                 "Meta API returned HTTP 400 at create_text_container")

    @patch("scripts.threads.meta_api.urllib.request.urlopen")
    def test_no_error_body_does_not_mask_http_error(self, send):
        send.side_effect=urllib.error.HTTPError(
            "https://graph.threads.net/me/threads",400,"Bad Request",{},None)
        with self.assertRaises(ThreadsApiError) as ctx:
            self.client.create_text_container("正常なテキスト")
        self.assertIn("HTTP 400 at create_text_container",str(ctx.exception))


if __name__=="__main__":
    unittest.main()
