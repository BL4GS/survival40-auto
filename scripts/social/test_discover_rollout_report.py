"""No-network tests for sampled Discover/OG triage, not Google eligibility."""
import json
from pathlib import Path
import tempfile
import unittest

from scripts.social import discover_rollout_report as d


def asset(ident, url):
    return {
        "article_id": ident,
        "article_url": url,
        "status": "assets_ready_not_published",
        "social_og_image": d.RAW + f"assets/social/og/{ident}.png",
        "instagram_image": d.RAW + f"assets/instagram/auto/{ident}.png",
    }


def row(ident, url, status, preview="LARGE_DECLARED_IN_HTML", noindex=False):
    return {
        "article_id": ident,
        "article_url": url,
        "status": status,
        "discover_metadata": {
            "html_large_image_preview_hint": preview,
            "html_noindex_hint": noindex,
        },
    }


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.u1 = d.SITE + "test-a/"
        self.u2 = d.SITE + "test-b/"
        self.og = {"site": d.SITE[:-1], "read_only": True, "items": [
            row(512, self.u1, "ORIGINAL_INSTAGRAM_CARD_WIDTH_UNVERIFIED"),
            row(516, self.u2, "EXACT_ORIGINAL_SOCIAL_CARD"),
        ]}
        self.manifest = {
            "brand": "Survival40",
            "source": "verified_Pinterest_static_feed",
            "publishing_enabled": False,
            "items": [asset(512, self.u1), asset(516, self.u2)],
        }

    def test_exact_portrait_is_stage_only_not_live_approval(self):
        result = d.summarize(self.og, self.manifest)
        self.assertEqual(result["sampled_articles"], 2)
        self.assertEqual(result["items"][0]["review_category"],
                         "KNOWN_PORTRAIT_OG_OPTIONAL_STAGE_ONLY_REVIEW")
        self.assertEqual(result["items"][1]["review_category"],
                         "ORIGINAL_LANDSCAPE_OG_DECLARED_NOT_GOOGLE_VERIFIED")
        self.assertFalse(result["wordpress_modified"])
        self.assertFalse(result["social_published"])
        self.assertFalse(result["actual_discover_impressions_verified"])
        self.assertFalse(result["remote_image_bytes_verified_by_this_join"])
        self.assertFalse(result["full_wordpress_article_inventory_covered"])
        self.assertIn("staging", result["items"][0]["recommendation"])

    def test_unknown_asset_cannot_be_claimed_usable(self):
        self.manifest["items"][0]["social_og_image"] = d.RAW + "assets/social/og/999.png"
        result = d.summarize(self.og, self.manifest)
        self.assertFalse(result["items"][0]["same_article_landscape_candidate_in_manifest"])
        self.assertIsNone(result["items"][0]["candidate_url"])
        self.assertEqual(result["items"][0]["review_category"],
                         "NO_SAFE_AUTOMATIC_OG_CONCLUSION")

    def test_noindex_and_preview_restriction_take_precedence(self):
        self.og["items"][0]["discover_metadata"]["html_noindex_hint"] = True
        self.og["items"][1]["discover_metadata"]["html_large_image_preview_hint"] = (
            "LARGE_NOT_ALLOWED_BY_HTML_DIRECTIVE_REVIEW")
        result = d.summarize(self.og, self.manifest)
        self.assertEqual(result["items"][0]["review_category"],
                         "HTML_NOINDEX_REQUIRES_REVIEW")
        self.assertEqual(result["items"][1]["review_category"],
                         "IMAGE_PREVIEW_DIRECTIVE_REQUIRES_REVIEW")

    def test_missing_html_preview_is_not_called_a_block(self):
        self.og["items"][0]["discover_metadata"][
            "html_large_image_preview_hint"] = "NOT_DECLARED_IN_HTML_HEADER_NOT_CHECKED"
        result = d.summarize(self.og, self.manifest)
        self.assertEqual(result["items"][0]["review_category"],
                         "KNOWN_PORTRAIT_OG_OPTIONAL_STAGE_ONLY_REVIEW")

    def test_transport_unknown_never_assumed_good_or_zero(self):
        self.og["items"][0] = {
            "article_id": 512, "article_url": self.u1,
            "status": "UNAVAILABLE_UNVERIFIED",
        }
        result = d.summarize(self.og, self.manifest)
        self.assertEqual(result["items"][0]["review_category"],
                         "LIVE_HTML_UNAVAILABLE_NEEDS_RECHECK")

    def test_duplicate_row_or_duplicate_manifest_rejected(self):
        self.og["items"].append(dict(self.og["items"][0]))
        with self.assertRaises(ValueError):
            d.summarize(self.og, self.manifest)
        self.og["items"].pop()
        self.manifest["items"].append(dict(self.manifest["items"][0]))
        with self.assertRaises(ValueError):
            d.summarize(self.og, self.manifest)

    def test_wrong_domain_and_manifests_fail_closed(self):
        for value in ("https://evil.test/article/", "https://www.survival40.com.evil/a/"):
            with self.subTest(url=value):
                self.og["items"][0]["article_url"] = value
                with self.assertRaises(ValueError):
                    d.summarize(self.og, self.manifest)
        self.og["items"][0]["article_url"] = self.u1
        self.manifest["publishing_enabled"] = True
        with self.assertRaises(ValueError):
            d.summarize(self.og, self.manifest)

    def test_writes_only_diagnostic_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "observed.json"
            manifest = Path(tmp) / "manifest.json"
            report = Path(tmp) / "report.json"
            src.write_text(json.dumps(self.og))
            manifest.write_text(json.dumps(self.manifest))
            actual = d.run(src, manifest, report)
            self.assertEqual(actual["sampled_articles"], 2)
            self.assertEqual(json.loads(report.read_text())["read_only"], True)


if __name__ == "__main__":
    unittest.main()
