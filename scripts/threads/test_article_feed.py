"""Read-only article feed and Shiori scheduled recurring promotions tests."""
import datetime as dt
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo
import json

from scripts.threads.article_feed import (
    ArticleSourceError, build_article_text, plain, require_article_url,
    select_recent, last_link_slot
)
from scripts.threads.compose import CONFIG
from scripts.threads.prepare_schedule import choose_copy
from scripts.threads.scheduled_publisher import verify_draft, publish


JST = ZoneInfo("Asia/Tokyo")


def source(post_id, local_time, title, slug):
    return {
        "id": post_id, "status": "publish",
        "date_gmt": local_time.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "title": {"rendered": title},
        "excerpt": {"rendered": "<p>Published excerpt from original article.</p>"},
        "content": {"rendered": "<p>" + "This is the public article content. " * 8 + "</p>"},
        "link": "https://www.survival40.com/" + slug + "/",
    }


class ArticleFeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))

    def test_html_to_plain_text(self):
        self.assertEqual(plain("<p>素直な<b>文章</b></p><script>evil</script>"), "素直な文章")
        self.assertEqual(plain(None), "")

    def test_strict_origin_url_and_canonical_paths(self):
        for url in (
            "http://www.survival40.com/test/",
            "https://survival40.com.evil.test/test/",
            "https://evil.test/test/",
            "https://www.survival40.com/",
            "https://www.survival40.com/?p=512",
            "https://www.survival40.com/test/?download=1",
            "https://www.survival40.com/path/subpath/",
            "https://www.survival40.com@evil.test/test/",
        ):
            with self.subTest(url=url), self.assertRaises(ArticleSourceError):
                require_article_url(url)
        self.assertEqual(require_article_url("https://www.survival40.com/test-slug/"),
                         "https://www.survival40.com/test-slug/")

    def test_wednesday_saturday_and_freshness_cutoff(self):
        wed = dt.datetime(2026, 10, 28, 20, 5, tzinfo=JST)
        old = source(45, dt.datetime(2026, 10, 24, 19, tzinfo=JST),
                     "古い記事です｜参考", "old-post")
        fresh = source(51, dt.datetime(2026, 10, 27, 9, tzinfo=JST),
                       "疲れた日でも食事を選ぶ方法", "new-food-post")
        future = source(55, dt.datetime(2026, 10, 29, 9, tzinfo=JST),
                        "未来の記事は不可", "future")
        draft = source(59, dt.datetime(2026, 10, 27, 9, tzinfo=JST),
                       "未公開記事", "draft")
        draft["status"] = "draft"
        self.assertEqual(select_recent([old, fresh, future, draft], wed)["id"], 51)
        self.assertEqual(select_recent([old], wed), None)
        sat = dt.datetime(2026, 10, 31, 20, 3, tzinfo=JST)
        self.assertEqual(select_recent([fresh], sat), None)
        self.assertEqual(last_link_slot(sat).date(), dt.date(2026, 10, 28))

    def test_recurring_link_only_evening_and_only_if_new_article(self):
        wed = dt.datetime(2026, 10, 28, 20, 5, tzinfo=JST)
        article = source(514, dt.datetime(2026, 10, 27, 9, tzinfo=JST),
                         "疲れたときに何を食べる？40代男性の食事選び", "40s-fatigue-food-meal-balance")
        with patch("scripts.threads.prepare_schedule.fetch_public_posts", return_value=[article]):
            prepared = choose_copy(wed, self.config, None)
        self.assertEqual(prepared["kind"], "article")
        self.assertEqual(prepared["article_id"], 514)
        self.assertEqual(prepared["article_url"], article["link"])
        self.assertEqual(prepared["text"], build_article_text({"title": prepared["article_title"], "url": prepared["article_url"]}))
        self.assertEqual(verify_draft(prepared, wed, self.config), prepared["text"])

        for changed in (
            {"article_url": "https://evil.test/post/"},
            {"article_id": None},
            {"article_title": "無関係のタイトル"},
            {"text": prepared["text"] + " 今すぐ購入"},
        ):
            with self.subTest(changed=changed), self.assertRaises((ValueError, ArticleSourceError)):
                verify_draft(dict(prepared, **changed), wed, self.config)

        with patch("scripts.threads.prepare_schedule.fetch_public_posts", return_value=[]), patch(
                "scripts.threads.prepare_schedule.gemini_generate",
                return_value="洗面台の小物がいつの間にか増えていて、何から片づけるか迷っています。"):
            prepared2 = choose_copy(wed, self.config, "fake-key")
        self.assertEqual(prepared2["kind"], "everyday")
        self.assertIsNone(prepared2["article_id"])
        self.assertEqual(verify_draft(prepared2, wed, self.config), prepared2["text"])

    def test_feed_failure_falls_back_to_persona_post(self):
        wed = dt.datetime(2026, 10, 28, 20, 5, tzinfo=JST)
        with patch("scripts.threads.prepare_schedule.fetch_public_posts",
                   side_effect=ArticleSourceError("offline")), patch(
                "scripts.threads.prepare_schedule.gemini_generate",
                return_value="洗面台の小物がいつの間にか増えていて、何から片づけるか迷っています。"):
            prepared = choose_copy(wed, self.config, "fake-key")
        self.assertEqual(prepared["kind"], "everyday")
        self.assertEqual(verify_draft(prepared, wed, self.config), prepared["text"])

    def test_per_article_reservation_precedes_meta_posts(self):
        wed = dt.datetime(2026, 10, 28, 20, 5, tzinfo=JST)
        article = source(514, dt.datetime(2026, 10, 27, 9, tzinfo=JST),
                         "疲れたときに何を食べる？40代男性の食事選び", "40s-fatigue-food-meal-balance")
        with patch("scripts.threads.prepare_schedule.fetch_public_posts", return_value=[article]):
            prepared = choose_copy(wed, self.config, None)
        env = {
            "GITHUB_EVENT_NAME": "schedule",
            "GITHUB_REPOSITORY": "BL4GS/survival40-auto",
            "GITHUB_REF": "refs/heads/main",
            "THREADS_ACCESS_TOKEN": "FAKE_TOKEN_FOR_UNIT_TEST_ONLY",
            "THREADS_USER_ID": "123",
            "GITHUB_TOKEN": "FAKE_GITHUB",
        }
        calls = []
        with (patch("scripts.threads.token_preflight.safe_get", return_value={}),
              patch("scripts.threads.token_preflight.validate_profile"),
              patch("scripts.threads.token_preflight.validate_debug_response"),
              patch("scripts.threads.scheduled_publisher.MetaThreadsClient") as client,
              patch("scripts.threads.scheduled_publisher.GithubLedger") as ledger):
            ledger.return_value.reserve.side_effect = lambda key, *args: (calls.append("reserve:" + key) or True)
            client.return_value.create_text_container.side_effect = lambda text: (calls.append("container") or "321")
            client.return_value.publish_container.side_effect = lambda x: (calls.append("publish") or "654")
            self.assertEqual(publish(prepared, wed, self.config, env), "654")
        self.assertEqual(calls, ["reserve:2026-10-28-evening", "reserve:article-514", "container", "publish"])


if __name__ == "__main__":
    unittest.main()
