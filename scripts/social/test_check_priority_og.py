"""Offline regression coverage for the optional 387/389/438/596 OG diagnostic."""
import unittest

from scripts.social import check_priority_og as audit
from scripts.social.check_og import INSTAGRAM_PREFIX


class PriorityOGTests(unittest.TestCase):
    def test_four_fixed_canonical_articles_only(self):
        self.assertEqual([ident for ident, _ in audit.TARGETS], [387, 389, 438, 596])
        self.assertTrue(all(
            audit.canonical(url) == url for _, url in audit.TARGETS
        ))

    def test_realistic_aioseo_article_images_flagged_without_image_fetch(self):
        requested = []
        def fake_fetch(url):
            requested.append(url)
            is_humidifier = "/40s-winter-dry-air-humidifier-guide/" in url
            image = (
                "https://secure.gravatar.com/avatar/sample?s=96"
                if "/40s-male-bad-breath-care/" in url or is_humidifier
                else "https://www26.a8.net/svt/bgt?aid=123&amp;wid=005"
            )
            og = ('<meta property="og:image" content="' +
                  INSTAGRAM_PREFIX + '596.png">' if is_humidifier else '')
            return (
                '<head><meta name="robots" content="max-image-preview:large">' + og +
                '<script type="application/ld+json">'
                '{"@context":"https://schema.org","@graph":['
                '{"@type":"BlogPosting","image":{"@type":"ImageObject",'
                '"url":"' + image + '"}}]}</script></head>'
            )
        result = audit.run(fetcher=fake_fetch)
        self.assertEqual(requested, [url for _, url in audit.TARGETS])
        self.assertEqual([row["status"] for row in result["items"]],
                         ["MISSING_OG_IMAGE", "MISSING_OG_IMAGE",
                          "MISSING_OG_IMAGE",
                          "ORIGINAL_INSTAGRAM_CARD_WIDTH_UNVERIFIED"])
        self.assertEqual(
            [row["discover_metadata"]["article_schema_image_source_hint"]
             for row in result["items"]],
            ["POSSIBLE_A8_AFFILIATE_IMAGE_REVIEW",
             "GRAVATAR_AVATAR_IMAGE_REVIEW",
             "POSSIBLE_A8_AFFILIATE_IMAGE_REVIEW",
             "GRAVATAR_AVATAR_IMAGE_REVIEW"],
        )
        self.assertTrue(result["read_only"])
        self.assertFalse(result["changed_site"])
        self.assertFalse(result["social_published"])
        self.assertFalse(result["google_discover_appearance_verified"])
        self.assertFalse(result["image_bytes_or_dimensions_verified"])
        self.assertNotIn("aid=123", str(result))
        self.assertEqual(result["items"][3]["discover_metadata"]
                         ["html_large_image_preview_hint"], "LARGE_DECLARED_IN_HTML")
        self.assertEqual(result["items"][3]["discover_metadata"]
                         ["image_bytes_or_dimensions_verified"], False)

    def test_one_unavailable_page_never_becomes_a_pass(self):
        def fake_fetch(url):
            if "/40s-male-bad-breath-care/" in url:
                raise TimeoutError("secret response body")
            return '<head><meta property="og:title" content="test"></head>'
        result = audit.run(fetcher=fake_fetch)
        self.assertEqual(result["items"][0]["status"], "MISSING_OG_IMAGE")
        self.assertEqual(result["items"][1]["status"], "UNAVAILABLE_UNVERIFIED")
        self.assertEqual(result["items"][1]["error_type"], "TimeoutError")
        self.assertNotIn("secret response body", str(result))
        self.assertEqual(result["items"][2]["status"], "MISSING_OG_IMAGE")
        self.assertEqual(result["items"][3]["status"], "MISSING_OG_IMAGE")


if __name__ == "__main__":
    unittest.main()
