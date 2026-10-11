import datetime as dt
import unittest
from unittest.mock import patch
from scripts.threads.articles import ArticleSourceError, plain_text, safe_article_url, select_article
from scripts.threads.compose_articles import make_prompt, validate_article_copy


NOW = dt.datetime(2026, 10, 11, 13, 0, tzinfo=dt.timezone.utc)
LONG_BODY = "<p>" + "忙しい日には少しだけ歩くことを心がけましょう。" * 18 + "</p>"


def post(post_id, date, url="https://survival40.com/articles/eye-care/", status="publish"):
    return {
        "id": post_id, "status": status, "date_gmt": date,
        "link": url, "title": {"rendered": "40代からの目の休ませ方"},
        "excerpt": {"rendered": "<p>忙しい方への生活情報。</p>"},
        "content": {"rendered": LONG_BODY},
    }


class WordPressArticleTests(unittest.TestCase):
    def test_plain_text_strips_html_and_scripts(self):
        self.assertEqual(plain_text("<p>目を休ませる</p><script>alert('x')</script> <b>工夫</b>"),
                         "目を休ませる 工夫")

    def test_article_url_must_remain_on_site(self):
        self.assertEqual(safe_article_url("https://survival40.com/articles/eye-care/"),
                         "https://survival40.com/articles/eye-care/")
        for url in ("https://evil.example/a", "http://survival40.com/test/",
                    "https://survival40.com.evil.example/test/",
                    "https://survival40.com/", "https://survival40.com/a?redirect=evil"):
            with self.assertRaises(ArticleSourceError):
                safe_article_url(url)

    def test_only_recent_published_article(self):
        posts = [
            post(5, "2026-10-10T23:00:00"),
            post(8, "2026-10-11T01:00:00", status="draft"),
            post(9, "2026-10-11T22:00:00"),  # future date
            post(10, "2026-10-10T02:00:00"),  # older than 24h
            post(11, "2026-10-11T04:00:00", url="https://evil.example/post"),
        ]
        self.assertEqual(select_article(posts, now=NOW)["id"], "5")

    def test_missing_article_skips(self):
        self.assertIsNone(select_article([post(1, "2026-10-09T09:00:00")], now=NOW))

    def test_ignore_short_and_incomplete_content(self):
        p = post(1, "2026-10-11T12:00:00")
        p["content"]["rendered"] = "<p>short</p>"
        self.assertIsNone(select_article([p], now=NOW))

    def test_article_copy_adds_only_verified_url(self):
        a = select_article([post(1, "2026-10-11T12:00:00")], now=NOW)
        body = "40代からの生活習慣について、無理なく続ける小さな工夫を記事にまとめました。忙しい日の休み方も、できることから見直してみませんか。"
        text = validate_article_copy(body, a)
        self.assertTrue(text.endswith(a["url"]))
        self.assertEqual(text.count(a["url"]), 1)
        self.assertNotIn("https://", body)
        self.assertIn("article_body_excerpt", make_prompt(a))

    def test_copy_rejects_extra_links_and_misleading_claims(self):
        a = select_article([post(1, "2026-10-11T12:00:00")], now=NOW)
        for text in (
            "この記事は参考になるので、https://evil.example/ から読んでくださいね。気軽に試してみましょう。",
            "この方法を続けると絶対に治るので、ぜひ試してみましょう。目を労る習慣を始めましょう。",
            "医師としておすすめします。どんな方でも取り入れやすい方法を紹介しているので、ぜひ読んでくださいね。",
        ):
            with self.assertRaises(ValueError):
                validate_article_copy(text, a)


if __name__ == "__main__":
    unittest.main()
