"""No-network regression tests for Article JSON-LD image source triage."""
import unittest
from scripts.social.schema_image_review import review_schema_images as review


class SchemaImageReviewTests(unittest.TestCase):
    def test_a8_banner_in_article_graph_is_flagged_without_fetching(self):
        html = ('<head><script type="application/ld+json">'
                '{"@context":"https://schema.org","@graph":[{"@type":"WebSite"},'
                '{"@type":"BlogPosting","image":{"@type":"ImageObject",'
                '"url":"https://www21.a8.net/svt/bgt?aid=123"}}]}'
                '</script></head>')
        r = review(html)
        self.assertEqual(r["article_schema_image_source_hint"],
                         "POSSIBLE_A8_AFFILIATE_IMAGE_REVIEW")
        self.assertEqual(r["article_schema_image_count"], 1)
        self.assertTrue(r["schema_images_checked"])
        self.assertNotIn("aid=123", str(r))

    def test_gravatar_avatar_in_article_is_review_only(self):
        html = ('<head><script type="application/ld+json">'
                '{"@type":"Article","image":"https://secure.gravatar.com/avatar/abc"}'
                '</script></head>')
        self.assertEqual(review(html)["article_schema_image_source_hint"],
                         "GRAVATAR_AVATAR_IMAGE_REVIEW")

    def test_valid_article_image_is_not_certified_large(self):
        html = ('<head><script type="application/ld+json">'
                '{"@type":"NewsArticle","image":["https://www.survival40.com/hero.jpg"]}'
                '</script></head>')
        r = review(html)
        self.assertEqual(r["article_schema_image_source_hint"],
                         "OTHER_ARTICLE_SCHEMA_IMAGE_DIMENSIONS_UNVERIFIED")
        self.assertFalse("image_bytes_or_dimensions_verified" in r)

    def test_non_article_schema_does_not_misclassify_author_avatar(self):
        html = ('<head><script type="application/ld+json">'
                '{"@type":"Person","image":"https://secure.gravatar.com/avatar/abc"}'
                '</script></head>')
        self.assertEqual(review(html)["article_schema_image_source_hint"],
                         "NO_ARTICLE_SCHEMA_IMAGE_OBSERVED")

    def test_body_json_ld_is_not_treated_as_head_metadata(self):
        html = ('<head></head><body><script type="application/ld+json">'
                '{"@type":"Article","image":"https://www21.a8.net/banner.png"}'
                '</script></body>')
        self.assertEqual(review(html)["article_schema_image_count"], 0)

    def test_malformed_json_is_unverified_not_safe(self):
        r = review('<head><script type="application/ld+json">{bad}</script></head>')
        self.assertFalse(r["schema_images_checked"])
        self.assertTrue(r["schema_parse_incomplete"])
        self.assertEqual(r["article_schema_image_source_hint"],
                         "SCHEMA_JSON_UNPARSEABLE_REVIEW")

    def test_oversized_json_ld_is_not_parsed(self):
        html = ('<head><script type="application/ld+json">' +
                '{"@type":"Article","image":"' + "x" * 65000 +
                '"}</script></head>')
        r = review(html)
        self.assertFalse(r["schema_images_checked"])
        self.assertEqual(r["article_schema_image_count"], 0)

    def test_valueless_script_type_does_not_break_read_only_audit(self):
        html = '<head><script type>not JSON-LD</script></head>'
        r = review(html)
        self.assertEqual(r["article_schema_image_count"], 0)
        self.assertFalse(r["schema_images_checked"])

    def test_no_script_is_observation_not_discover_verdict(self):
        r = review('<head><meta name="robots" content="max-image-preview:large"></head>')
        self.assertEqual(r["schema_json_ld_scripts_seen"], 0)
        self.assertEqual(r["article_schema_image_source_hint"],
                         "NO_ARTICLE_SCHEMA_IMAGE_OBSERVED")
        self.assertIn("not proof", r["schema_review_note"])


if __name__ == "__main__":
    unittest.main()
