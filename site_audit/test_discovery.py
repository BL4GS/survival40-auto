import unittest

from site_audit.discovery import analyze_discovery, public_path


def post(post_id, links=""):
    return {
        "id": post_id, "status": "publish",
        "link": f"https://www.survival40.com/subject-{post_id}/",
        "content": {"rendered": "<p>Some reader article</p>" + links},
    }


class InternalDiscoveryTests(unittest.TestCase):
    def test_public_path_is_strict_same_origin_but_accepts_canonical_alias(self):
        self.assertEqual(public_path("https://survival40.com/topic/?ref=nav#top"), "/topic")
        self.assertEqual(public_path("/topic/"), "/topic")
        self.assertEqual(public_path("https://www.survival40.com/topic"), "/topic")
        for bad in ("http://www.survival40.com/topic",
                    "https://www.survival40.com.evil.test/topic",
                    "https://user:secret@www.survival40.com/topic",
                    "https://evil.test/topic", "mailto:someone@example.com",
                    "javascript:alert(1)", None):
            self.assertIsNone(public_path(bad), bad)

    def test_links_from_homepage_and_article_body_are_distinct(self):
        posts = [
            post(10, '<a href="/subject-20/?src=read">20</a>'),
            post(20, '<a href="https://evil.test/">offsite</a><a href="/subject-20/">self</a>'),
            post(30),
        ]
        home = '<nav><a href="/subject-10/">10</a></nav><main><a href="https://survival40.com/subject-20/#read">20</a></main>'
        result = analyze_discovery(posts, home)
        self.assertEqual(result["posts_in_inventory"], 3)
        self.assertEqual(result["homepage_linked_ids"], [10, 20])
        self.assertEqual(result["not_linked_on_homepage_ids"], [30])
        self.assertEqual(result["body_inbound_counts"], {"10": 0, "20": 1, "30": 0})
        self.assertEqual(result["not_linked_from_home_or_post_body_ids"], [30])
        self.assertEqual(result["articles_with_no_body_outgoing_ids"], [20, 30])

    def test_homepage_unavailable_is_not_reported_as_zero_links(self):
        results = analyze_discovery([post(1), post(2)])
        self.assertFalse(results["homepage_inspected"])
        self.assertIsNone(results["homepage_linked_ids"])
        self.assertIsNone(results["not_linked_from_home_or_post_body_ids"])
        self.assertEqual(results["no_other_post_body_inbound_ids"], [1, 2])

    def test_ignores_draft_and_unknown_other_post_links(self):
        posts = [
            post(1, '<a href="/subject-5/">unpublished</a><a href="/subject-2/">published</a>'),
            post(2),
            {"id": 5, "status": "draft", "link": "https://www.survival40.com/subject-5/",
             "content": {"rendered": '<a href="/subject-1/">ignored</a>'}},
        ]
        out = analyze_discovery(posts, "<a href='/subject-5/'>draft</a>")
        self.assertEqual(out["posts_in_inventory"], 2)
        self.assertEqual(out["body_inbound_counts"], {"1": 0, "2": 1})
        self.assertEqual(out["homepage_links_to_published_posts"], 0)


if __name__ == "__main__":
    unittest.main()
