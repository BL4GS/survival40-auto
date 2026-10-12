import unittest

from production_preflight.baseline import snapshot
from production_preflight.monitor import (
    WatchFailure, check_homepage, check_probe, NAVIGATOR, REQUIRED_UI,
)


def published(idx):
    return {
        "id": idx, "status": "publish",
        "link": "https://www.survival40.com/example-" + str(idx) + "/",
        "title": {"rendered": "40代の暮らしガイド " + str(idx)},
        "content": {"rendered": "<p>公開済みの記事本文 " + str(idx) + "</p>"},
    }


def fixtures():
    posts = [published(i) for i in range(1, 24)]
    before = snapshot(posts, len(posts))
    markup = ("".join(REQUIRED_UI)
              + "".join('<a href="/example-' + str(i) + '/">記事</a>'
                        for i in range(1, 24)))
    pages = {"homepage": 200, "oldest": 200, "newest": 200}
    images = {name: 200 for name in NAVIGATOR}
    return before, posts, markup, pages, images


class PublicReleaseWatchTests(unittest.TestCase):
    def test_unchanged_snapshot_and_all_public_links_are_pass(self):
        before, posts, html, pages, images = fixtures()
        result = check_probe(before, posts, html, pages, images)
        self.assertEqual(result["public_articles_unchanged"], 23)
        self.assertEqual(result["homepage"]["linked_published"], 23)
        self.assertEqual(result["navigator_images_available"], 4)
        self.assertTrue(result["no_production_writes"])
        self.assertIn("16_private_drafts", result["requires_separate_verification"])

    def test_missing_homepage_article_link_is_failure(self):
        before, posts, html, pages, images = fixtures()
        html = html.replace('<a href="/example-23/">記事</a>', "")
        with self.assertRaisesRegex(WatchFailure, "lost published post links"):
            check_probe(before, posts, html, pages, images)

    def test_missing_shiori_marker_is_failure(self):
        before, posts, html, pages, images = fixtures()
        html = html.replace('class="s40-home-guide"', "")
        with self.assertRaisesRegex(WatchFailure, "homepage UI"):
            check_probe(before, posts, html, pages, images)

    def test_post_body_change_refuses_success(self):
        before, posts, html, pages, images = fixtures()
        posts[0]["content"]["rendered"] = "<p>Unexpected edit</p>"
        with self.assertRaisesRegex(WatchFailure, "article identifiers"):
            check_probe(before, posts, html, pages, images)

    def test_http_error_on_image_or_page_refuses_success(self):
        before, posts, html, pages, images = fixtures()
        images["normal"] = 404
        with self.assertRaisesRegex(WatchFailure, "Navigator image"):
            check_probe(before, posts, html, pages, images)
        images["normal"] = 200
        pages["homepage"] = 507
        with self.assertRaisesRegex(WatchFailure, "Public page"):
            check_probe(before, posts, html, pages, images)

    def test_missing_image_check_is_not_assumed_healthy(self):
        before, posts, html, pages, images = fixtures()
        del images["caution"]
        with self.assertRaisesRegex(WatchFailure, "were not inspected"):
            check_probe(before, posts, html, pages, images)

    def test_offsite_link_does_not_count_as_published(self):
        before, posts, html, pages, images = fixtures()
        bad = html.replace('<a href="/example-20/">記事</a>',
                           '<a href="https://www.survival40.com.evil.test/example-20/">記事</a>')
        with self.assertRaises(WatchFailure):
            check_probe(before, posts, bad, pages, images)

    def test_wrong_expected_public_article_count_fails_closed(self):
        before, posts, html, pages, images = fixtures()
        before["public_post_count"] = 24
        with self.assertRaises(ValueError):
            check_probe(before, posts, html, pages, images)

if __name__ == "__main__":
    unittest.main()
