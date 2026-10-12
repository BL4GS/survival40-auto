import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

from editorial_intelligence import deliver

def report():
    return {
        "schema": "survival40.wp_plan_handoff.v1",
        "wp_posts_written": 0, "threads_posts_written": 0,
        "ready_to_publish": False,
        "plans": [{
            "topic_id": "s40-abcdef0123456789abcd",
            "stage": "needs_independent_source_research",
            "plugin_planner_input": {
                "title": "40代男性の白髪染めシャンプーの仕組みと注意点",
                "amazon_query": "",
            },
            "editorial": {"verified_sources": 0, "sources_checked": False},
            "safety": {"publish_authorized": False, "no_affiliate_assigned": True},
        }]
    }

class Response:
    status = 202
    def __init__(self, reply): self.reply = reply
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, limit):
        return json.dumps(self.reply).encode("utf-8")

class FakeOpener:
    def __init__(self, reply):
        self.reply = reply
        self.calls = 0
        self.last = None
    def open(self, request, timeout):
        self.calls += 1
        self.last = request
        return Response(self.reply)

class DeliveryTests(unittest.TestCase):
    def test_default_disabled_does_not_read_file_or_contact_network(self):
        with patch.dict("os.environ", {"S40_WP_PLAN_DELIVERY_ENABLED": "false"}), patch(
            "editorial_intelligence.deliver.INPUT",
            pathlib.Path("/there-is-no-file-here.json")
        ), patch("editorial_intelligence.deliver.urllib.request.build_opener") as net:
            deliver.main()
            net.assert_not_called()

    def test_accepts_one_plan_without_auth_leak_in_output(self):
        fake = FakeOpener({"accepted": 1, "duplicate": 0,
                           "held": [], "wp_posts_created": 0,
                           "ready_to_publish": False})
        result = deliver.deliver(report(), "wp_editorial_admin", "secret-not-for-logs", opener=fake)
        self.assertEqual(result["accepted"], 1)
        self.assertEqual(fake.calls, 1)
        self.assertEqual(fake.last.get_method(), "POST")
        self.assertIn("survival40.com/index.php", fake.last.full_url)
        self.assertNotIn("secret-not-for-logs", fake.last.full_url)
        self.assertTrue(fake.last.get_header("Authorization").startswith("Basic "))

    def test_replay_is_reconciled_not_retried(self):
        fake = FakeOpener({"accepted": 0, "duplicate": 1,
                           "held": [], "wp_posts_created": 0,
                           "ready_to_publish": False})
        result = deliver.deliver(report(), "admin", "application-password", opener=fake)
        self.assertEqual(result["duplicate"], 1)
        self.assertEqual(fake.calls, 1)

    def test_redirect_never_forwards_auth(self):
        handler = deliver.NoRedirects()
        with self.assertRaises(deliver.DeliveryError):
            handler.redirect_request(None, None, 302, "redirect", {}, "https://evil.test/")

    def test_rejects_dangerous_plan_before_network(self):
        bads = []
        for key, value in (("ready_to_publish", True), ("wp_posts_written", 1),
                           ("schema", "not-survival40"), ("threads_posts_written", 1)):
            item = report()
            item[key] = value
            bads.append(item)
        x = report()
        x["plans"][0]["plugin_planner_input"]["amazon_query"] = "buy-this"
        bads.append(x)
        x = report()
        x["plans"][0]["safety"]["publish_authorized"] = True
        bads.append(x)
        for item in bads:
            with self.subTest(item=item):
                fake = FakeOpener({"accepted": 1})
                with self.assertRaises(deliver.DeliveryError):
                    deliver.deliver(item, "admin", "key", opener=fake)
                self.assertEqual(fake.calls, 0)

    def test_refuses_bad_acknowledgement(self):
        for response in (
            {"accepted": 1, "duplicate": 0, "held": [],
             "wp_posts_created": 1, "ready_to_publish": False},
            {"accepted": 0, "duplicate": 0, "held": [],
             "wp_posts_created": 0, "ready_to_publish": False},
            {"accepted": 1, "duplicate": 0, "held": [],
             "wp_posts_created": 0, "ready_to_publish": True},
        ):
            with self.subTest(response=response):
                with self.assertRaises(deliver.DeliveryError):
                    deliver.deliver(report(), "admin", "key", opener=FakeOpener(response))

    def test_no_credentials_refused_without_network(self):
        fake=FakeOpener({"accepted":1})
        with self.assertRaises(deliver.DeliveryError):
            deliver.deliver(report(), "", "", opener=fake)
        self.assertEqual(fake.calls,0)

    def test_empty_plan_does_not_send_any_request(self):
        item=report()
        item["plans"]=[]
        fake=FakeOpener({"accepted": 0})
        out=deliver.deliver(item,"admin","key",opener=fake)
        self.assertEqual(fake.calls,0)
        self.assertEqual(out["accepted"],0)

if __name__ == "__main__":
    unittest.main()
