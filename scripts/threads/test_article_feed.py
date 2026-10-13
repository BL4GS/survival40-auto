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

    def test_existing_twenty_hour_slots_are_persona_after_october_24(self):
        wed = dt.datetime(2026, 10, 28, 20, 5, tzinfo=JST)
        with patch("scripts.threads.prepare_schedule.gemini_generate",
                   return_value="洗面台の小物がいつの間にか増えていて、何から片づけるか迷っています。"):
            prepared = choose_copy(wed, self.config, "fake-key")
        self.assertEqual(prepared["kind"], "everyday")
        self.assertIsNone(prepared["article_id"])
        self.assertIsNone(prepared["article_url"])
        self.assertEqual(verify_draft(prepared, wed, self.config), prepared["text"])

    def test_no_public_article_lookup_during_persona_slot(self):
        wed = dt.datetime(2026, 10, 28, 20, 5, tzinfo=JST)
        with (patch("scripts.threads.prepare_schedule.gemini_generate",
                    return_value="洗面台の小物がいつの間にか増えていて、何から片づけるか迷っています。"),
              patch("scripts.threads.article_feed.fetch_public_posts",
                    side_effect=ArticleSourceError("Do not access public API"))):
            prepared = choose_copy(wed, self.config, "fake-key")
        self.assertEqual(prepared["kind"], "everyday")
        self.assertEqual(verify_draft(prepared, wed, self.config), prepared["text"])



if __name__ == "__main__":
    unittest.main()
