"""Unit tests for a separate, fail-closed 22:00 article promotion slot."""
import datetime as dt
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from scripts.threads.scheduled_article_publisher import (
    allowed_clock, latest_evening_article, prepare, validate_prepared,
    publish_once,
)
from scripts.threads.article_feed import ArticleSourceError

JST = ZoneInfo("Asia/Tokyo")
ENV = {
    "GITHUB_EVENT_NAME": "schedule",
    "GITHUB_REPOSITORY": "BL4GS/survival40-auto",
    "GITHUB_REF": "refs/heads/main",
    "THREADS_ACCESS_TOKEN": "A_TEST_ACCESS_TOKEN_ONLY",
    "THREADS_USER_ID": "123456",
    "GITHUB_TOKEN": "A_TEST_GITHUB_TOKEN",
}


def when(day=19, hour=22, minute=5):
    return dt.datetime(2026, 10, day, hour, minute, tzinfo=JST)


def item(pid=901, day=19, hour=21, minute=0, *, state="publish",
         url="https://www.survival40.com/40s-healthy-foods/"):
    local = when(day, hour, minute)
    return {
        "id": pid,
        "status": state,
        "date_gmt": local.astimezone(dt.timezone.utc).isoformat(),
        "link": url,
        "title": {"rendered": "疲れたときに考えたい食事と主菜の選び方"},
        "content": {"rendered": "<p>" + "実際に公表済みの記事テキストです。" * 12 + "</p>"},
    }


class AdditionalArticleTests(unittest.TestCase):
    def test_time_gate_avoids_early_or_wrong_hour(self):
        self.assertFalse(allowed_clock(when(day=18)))
        self.assertFalse(allowed_clock(when(day=19, hour=20)))
        self.assertFalse(allowed_clock(when(day=19, hour=21)))
        self.assertTrue(allowed_clock(when()))
        self.assertTrue(allowed_clock(when(day=19, hour=22, minute=59)))

    def test_only_todays_published_article_after_evening(self):
        today = item()
        self.assertEqual(latest_evening_article([today], when())["id"], 901)
        self.assertIsNone(latest_evening_article([item(day=18)], when()))
        self.assertIsNone(latest_evening_article([item(hour=20, minute=30)], when()))
        self.assertIsNone(latest_evening_article([item(hour=22, minute=30)], when()))
        self.assertIsNone(latest_evening_article([item(state="future")], when()))
        self.assertIsNone(latest_evening_article([item(url="https://evil.test/post/")], when()))
        self.assertIsNone(latest_evening_article([], when()))

    def test_prepare_exact_late_slot_article_and_verify(self):
        a = prepare(when(), [item()])
        self.assertEqual(a["slot"], "late-article")
        self.assertEqual(a["kind"], "article")
        self.assertEqual(a["article_id"], 901)
        self.assertIn("【PR】", a["text"])
        self.assertEqual(validate_prepared(a, when()), a["text"])
        for tamper in (
            {"article_id": "901"},
            {"article_url": "https://evil.test/post/"},
            {"article_title": "別の記事"},
            {"text": a["text"] + "買うべき"},
            {"generated_at_jst": "2026-10-19T20:00:00+09:00"},
            {"source_published_jst": "2026-10-18T21:00:00+09:00"},
            {"date_jst": "2026-10-20"},
            {"publish": True},
            {"status": "published"},
        ):
            with self.subTest(tamper=tamper), self.assertRaises((ValueError, ArticleSourceError)):
                validate_prepared(dict(a, **tamper), when())
        with self.assertRaises(ValueError):
            validate_prepared(a, when(hour=21))

    def test_publishing_never_happens_on_manual_preview_or_bad_identity(self):
        post = prepare(when(), [item()])
        with patch("scripts.threads.scheduled_article_publisher.MetaThreadsClient") as client:
            for env in (dict(ENV, GITHUB_EVENT_NAME="workflow_dispatch"),
                        dict(ENV, GITHUB_REF="refs/heads/not-main"),
                        dict(ENV, THREADS_ACCESS_TOKEN="")):
                with self.assertRaises(ValueError):
                    publish_once(post, when(), env)
            client.assert_not_called()

    def test_preflight_and_both_reservations_precede_meta(self):
        post = prepare(when(), [item()])
        calls = []
        with (patch("scripts.threads.scheduled_article_publisher.safe_get", return_value={}),
              patch("scripts.threads.scheduled_article_publisher.validate_profile"),
              patch("scripts.threads.scheduled_article_publisher.validate_debug_response"),
              patch("scripts.threads.scheduled_article_publisher.MetaThreadsClient") as meta,
              patch("scripts.threads.scheduled_article_publisher.GithubLedger") as ledger):
            ledger.return_value.reserve.side_effect = (
                lambda key, *args: (calls.append("reserve:" + key) or True)
            )
            meta.return_value.publish_text.side_effect = (
                lambda txt: (calls.append("auto_publish") or "777")
            )
            self.assertEqual(publish_once(post, when(), ENV), "777")
            self.assertEqual(calls, [
                "reserve:2026-10-19-late-article", "reserve:article-901",
                "auto_publish"
            ])
            meta.return_value.publish_text.assert_called_once_with(post["text"])
            meta.return_value.publish_container.assert_not_called()
            meta.return_value.create_text_container.assert_not_called()
            self.assertEqual(ledger.return_value.mark_published.call_count, 2)

    def test_existing_article_is_never_posted_again(self):
        post = prepare(when(), [item()])
        with (patch("scripts.threads.scheduled_article_publisher.safe_get", return_value={}),
              patch("scripts.threads.scheduled_article_publisher.validate_profile"),
              patch("scripts.threads.scheduled_article_publisher.validate_debug_response"),
              patch("scripts.threads.scheduled_article_publisher.MetaThreadsClient") as meta,
              patch("scripts.threads.scheduled_article_publisher.GithubLedger") as ledger):
            ledger.return_value.reserve.side_effect = [True, False]
            self.assertIsNone(publish_once(post, when(), ENV))
            meta.return_value.publish_text.assert_not_called()
            meta.return_value.create_text_container.assert_not_called()
            meta.return_value.publish_container.assert_not_called()


if __name__ == "__main__":
    unittest.main()
