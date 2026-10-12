import copy
import unittest
from production_preflight.baseline import snapshot, compare


def article(post_id, title="40代からの暮らしの見直し", html="<p>生活習慣の基本。</p>"):
    return {"id": post_id, "status": "publish",
            "link": "https://survival40.com/article-%d/" % post_id,
            "title": {"rendered": title}, "content": {"rendered": html}}


class PublicBaselineTests(unittest.TestCase):
    def test_article_content_fingerprints(self):
        out = snapshot([article(3), article(5)], 2)
        self.assertEqual(out["public_post_count"], 2)
        self.assertEqual(len(out["articles"][0]["content_sha256"]), 64)
        self.assertEqual(out["production_writes"], 0)
        self.assertIn("draft_and_scheduled_posts", out["requires_admin_verification"])

    def test_content_changes_detected_with_no_article_text_leak(self):
        before = snapshot([article(3), article(5)])
        after = snapshot([article(3), article(5, html="<p>変更された内容</p>")])
        result = compare(before, after)
        self.assertEqual(result["changed_content"], [5])
        self.assertEqual(result["added"], [])
        self.assertEqual(result["removed"], [])
        self.assertNotIn("変更された内容", str(after))

    def test_added_deleted_posts_detected(self):
        before = snapshot([article(1), article(2)])
        after = snapshot([article(2), article(3)])
        diff = compare(before, after)
        self.assertEqual(diff["removed"], [1])
        self.assertEqual(diff["added"], [3])

    def test_duplicate_and_nonpublished_rejected(self):
        for posts in ([], [article(1), article(1)], [dict(article(1), status="draft")]):
            with self.subTest(posts=posts), self.assertRaises(ValueError):
                snapshot(posts)

    def test_external_url_rejected(self):
        post = article(1)
        post["link"] = "https://not-survival40.example/page/"
        with self.assertRaises(ValueError):
            snapshot([post])


if __name__ == "__main__":
    unittest.main()
