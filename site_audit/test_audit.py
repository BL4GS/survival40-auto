import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

from site_audit.audit import (
    AuditSourceError, MAX_CHECKED_PERMALINKS,
    evaluate, fetch_posts, plain, probe_public_pages, public_get,
    safe_post_url, write_reports,
)

def article(post_id, title="40代からの生活を整える方法", body=None):
    return {
        "id": post_id,
        "status": "publish",
        "title": {"rendered": title},
        "link": f"https://survival40.com/example-{post_id}/",
        "excerpt": {"rendered": "<p>無理なく続けるヒント。</p>"},
        "content": {"rendered": body or "<p>" + "いつもの習慣を少し整える方法を考える。" * 27 + "</p>"},
    }


class PublicSiteAuditTests(unittest.TestCase):
    def test_no_affiliate_link_is_not_error(self):
        result = evaluate([article(11)])
        self.assertEqual(result["post_count"], 1)
        self.assertIn("No-ad articles are valid", result["advertising_policy"])
        self.assertFalse(any("affiliate" in f["code"] for f in result["findings"]))

    def test_duplication_and_short_body_are_advisory(self):
        posts = [article(5, body="<p>短い本文</p>"), article(6)]
        result = evaluate(posts)
        codes = [f["code"] for f in result["findings"]]
        self.assertIn("duplicate_title", codes)
        self.assertIn("short_content", codes)

    def test_health_claim_is_manual_review_signal(self):
        p = article(1, body="<p>" + "必ず治る。" + "通常の説明文です。" * 50 + "</p>")
        findings = evaluate([p])["findings"]
        self.assertTrue(any(f["code"] == "strong_health_claim" and f["severity"] == "review" for f in findings))

    def test_decorative_images_are_only_info(self):
        result = evaluate([article(1, body="<p>生活習慣を少しずつ整えてみましょう。</p>" * 20 +
                           '<img src="/decorative.png" alt="">')])
        self.assertEqual(result["image_alt_gaps"], 1)
        self.assertEqual(next(f["severity"] for f in result["findings"] if f["code"] == "missing_image_alt"), "info")

    def test_title_parser_does_not_include_script(self):
        self.assertEqual(plain("<p>こんにちは</p><script>danger</script><p>世界</p>"), "こんにちは 世界")

    def test_offsite_and_url_credentials_rejected(self):
        for url in ("http://survival40.com/test/", "https://bad.example/test/",
                    "https://survival40.com.evil.test/foo", "https://survival40.com/",
                    "https://survival40.com/?page=1",
                    "https://user:password@survival40.com/test/"):
            with self.assertRaises(ValueError):
                safe_post_url(url)

    def test_probe_only_bounded_first_articles(self):
        posts = [article(i) for i in range(1, 100)]
        with patch("site_audit.audit.public_get", return_value=(200, {}, b"ok")) as req:
            pages = probe_public_pages(posts)
        self.assertEqual(len(pages), MAX_CHECKED_PERMALINKS + 1)
        self.assertEqual(req.call_count, MAX_CHECKED_PERMALINKS + 1)
        self.assertEqual(pages[0]["url"], "https://survival40.com/")

    def test_distinguishes_frontend_navigation_links_from_rest_article_text(self):
        posts = [article(1), article(2)]
        def simulated_get(url, **kwargs):
            if url.endswith("/example-1/"):
                return (200, {}, b'<html><nav><a href="/example-2/">Related</a></nav></html>')
            return (200, {}, b'<html><p>ok</p></html>')
        with patch("site_audit.audit.public_get", side_effect=simulated_get):
            probes = probe_public_pages(posts)
        self.assertEqual(probes[1]["rendered_other_post_links"], 1)
        self.assertEqual(probes[2]["rendered_other_post_links"], 0)

    def test_public_api_read_with_no_mutation(self):
        posts = [article(i) for i in (1, 2)]
        raw = json.dumps(posts).encode("utf-8")
        with patch("site_audit.audit.public_get",
                   return_value=(200, {"Content-Type": "application/json; charset=UTF-8",
                                       "X-WP-Total": "2"}, raw)) as get:
            actual, total = fetch_posts()
        self.assertEqual(len(actual), 2)
        self.assertEqual(total, 2)
        self.assertEqual(get.call_count, 1)
        self.assertIn("status=publish", get.call_args.args[0])
        self.assertIn("rest_route=", get.call_args.args[0])

    def test_http_failure_fails_closed(self):
        with patch("site_audit.audit.public_get", return_value=(403, {}, b"")):
            with self.assertRaises(AuditSourceError):
                fetch_posts()

    def test_reports_contain_no_rewrite_instruction(self):
        report = evaluate([article(1)])
        report["generated_at_utc"] = "2026-10-12T00:00:00+00:00"
        report["page_checks"] = [{"url": "https://survival40.com/", "status": 200, "outcome": "ok"}]
        with tempfile.TemporaryDirectory() as directory:
            write_reports(report, pathlib.Path(directory))
            markdown = (pathlib.Path(directory) / "audit.md").read_text(encoding="utf-8")
            data = json.loads((pathlib.Path(directory) / "audit.json").read_text(encoding="utf-8"))
            self.assertIn("No WordPress updates", markdown)
            self.assertEqual(data["post_count"], 1)


if __name__ == "__main__":
    unittest.main()
