"""No-network tests of Survival40 public Open Graph social cards."""
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from scripts.social import check_og as og


class OGTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.feed, self.report = root / "feed.xml", root / "report.json"
        channel = ET.Element("rss", {"version": "2.0"})
        ch = ET.SubElement(channel, "channel")
        for i in (512, 516):
            entry = ET.SubElement(ch, "item")
            ET.SubElement(entry, "link").text = (
                f"https://www.survival40.com/article-{i}/")
            ET.SubElement(entry, "enclosure", {"url": og.PIN_PREFIX + f"{i}.png",
                                               "type": "image/png"})
        self.feed.write_bytes(ET.tostring(channel))

    def test_discover_large_preview_present_as_html_hint_only(self):
        item = og.source_items(self.feed)[0]
        html = (
            '<head><meta name="robots" content="index, max-image-preview:large">'
            '<meta property="og:image" content="' + item["expected_social_image"] + '">'
            '<meta property="og:image:width" content="1200">'
            '<meta property="og:image:height" content="630"></head>'
        )
        result = og.inspect(item, html)["discover_metadata"]
        self.assertEqual(result["html_large_image_preview_hint"], "LARGE_DECLARED_IN_HTML")
        self.assertFalse(result["discover_appearance_checked"])
        self.assertFalse(result["image_bytes_or_dimensions_verified"])
        self.assertEqual(result["og_image_width_claim"], ["1200"])
        self.assertEqual(result["og_image_height_claim"], ["630"])

    def test_discover_unknown_is_not_called_blocked(self):
        item = og.source_items(self.feed)[0]
        result = og.inspect(item, "<head></head>")["discover_metadata"]
        self.assertEqual(
            result["html_large_image_preview_hint"],
            "NOT_DECLARED_IN_HTML_HEADER_NOT_CHECKED",
        )
        self.assertFalse(result["http_x_robots_tag_checked"])
        self.assertFalse(result["schema_images_checked"])

    def test_discover_standard_or_none_and_conflicts_are_review_only(self):
        item = og.source_items(self.feed)[0]
        cases = [
            ('<meta name="robots" content="max-image-preview:none">',
             "LARGE_NOT_ALLOWED_BY_HTML_DIRECTIVE_REVIEW"),
            ('<meta name="googlebot" content="max-image-preview:standard">',
             "LARGE_NOT_ALLOWED_BY_HTML_DIRECTIVE_REVIEW"),
            ('<meta name="robots" content="max-image-preview:large">'
             '<meta name="googlebot" content="max-image-preview:none">',
             "CONFLICTING_HTML_PREVIEW_DIRECTIVES_REVIEW"),
        ]
        for snippet, expectation in cases:
            with self.subTest(snippet=snippet):
                result = og.inspect(item, "<head>" + snippet + "</head>")
                self.assertEqual(
                    result["discover_metadata"]["html_large_image_preview_hint"],
                    expectation,
                )

    def test_discover_noindex_signal_is_evidence_not_eligibility(self):
        item = og.source_items(self.feed)[0]
        result = og.inspect(
            item, '<head><meta name="robots" content="noindex, max-image-preview:large">'
                  '</head>'
        )["discover_metadata"]
        self.assertTrue(result["html_noindex_hint"])
        self.assertFalse(result["google_indexing_checked"])
        self.assertFalse(result["discover_appearance_checked"])

    def test_missing_og_stays_explicit(self):
        data = og.run(self.feed, self.report, fetcher=lambda u: (
            '<html><head><meta property="og:title" content="記事">'
            '<meta name="twitter:card" content="summary_large_image"></head></html>'))
        self.assertEqual(data["checked"], 2)
        self.assertFalse(data["all_original_og_verified"])
        self.assertEqual([i["status"] for i in data["items"]],
                         ["MISSING_OG_IMAGE", "MISSING_OG_IMAGE"])
        self.assertTrue(data["read_only"])
        self.assertTrue(self.report.is_file())

    def test_exact_image_works_even_with_reversed_attribute_order(self):
        item = og.source_items(self.feed)[0]
        html = ('<html><head><meta content="' + item["expected_social_image"] +
                '" property="og:image"><meta name="twitter:image" content="https://example.com/a.jpg">'
                '</head></html>')
        result = og.inspect(item, html)
        self.assertEqual(result["status"], "EXACT_ORIGINAL_SOCIAL_CARD")
        self.assertEqual(len(result["twitter_images"]), 1)

    def test_known_original_instagram_og_image_is_not_unknown_or_missing(self):
        item = og.source_items(self.feed)[0]
        image = og.INSTAGRAM_PREFIX + str(item["article_id"]) + ".png"
        html = ('<head><meta property="og:image" content="' + image +
                '"><meta name="twitter:image" content="' + image +
                '"></head>')
        result = og.inspect(item, html)
        self.assertEqual(result["status"], "ORIGINAL_INSTAGRAM_CARD_WIDTH_UNVERIFIED")
        self.assertEqual(result["og_images"], [image])
        self.assertFalse(result["discover_metadata"]["image_bytes_or_dimensions_verified"])

    def test_wrong_article_instagram_og_is_not_accepted(self):
        item = og.source_items(self.feed)[0]
        wrong = og.INSTAGRAM_PREFIX + "9999.png"
        result = og.inspect(
            item, '<head><meta property="og:image" content="' + wrong + '"></head>'
        )
        self.assertEqual(result["status"], "OTHER_IMAGE_REVIEW")

    def test_known_instagram_cards_still_do_not_verify_discover_width(self):
        def fetcher(url):
            number = "512" if "/article-512/" in url else "516"
            return ('<head><meta property="og:image" content="' +
                    og.INSTAGRAM_PREFIX + number + '.png"></head>')
        output = og.run(self.feed, self.report, fetcher=fetcher)
        self.assertTrue(output["all_original_og_verified"])
        self.assertFalse(output["all_discover_image_width_verified"])
        self.assertEqual(len(output["items"]), 2)

    def test_another_image_is_review_not_automatically_banner(self):
        item = og.source_items(self.feed)[0]
        result = og.inspect(item, '<head><meta property="og:image" '
                            'content="https://cdn.example.com/article.jpg"></head>')
        self.assertEqual(result["status"], "OTHER_IMAGE_REVIEW")

    def test_multiple_og_images_is_not_pass(self):
        item = og.source_items(self.feed)[0]
        url = item["expected_social_image"]
        result = og.inspect(item, f'<head><meta property="og:image" content="{url}">'
                            f'<meta property="og:image" content="{url}"></head>')
        self.assertEqual(result["status"], "MULTIPLE_OG_IMAGES_REVIEW")

    def test_html_body_meta_ignored(self):
        item = og.source_items(self.feed)[0]
        html = f'<head></head><body><meta property="og:image" content="{item["expected_social_image"]}"></body>'
        result = og.inspect(item, html)
        self.assertEqual(result["status"], "MISSING_OG_IMAGE")

    def test_no_network_failure_does_not_claim_zero_or_valid(self):
        def broken(_):
            raise TimeoutError("bad network")
        report = og.run(self.feed, self.report, fetcher=broken)
        self.assertFalse(report["all_original_og_verified"])
        self.assertEqual(report["items"][0]["status"], "UNAVAILABLE_UNVERIFIED")
        self.assertNotIn("bad network", str(report))

    def test_raw_url_controls_are_rejected_before_urlsplit_normalization(self):
        # Python urlsplit() strips these characters and would otherwise
        # accept the altered URL as a canonical public article link.
        clean = "https://www.survival40.com/article-512/"
        self.assertEqual(og.canonical(clean), clean)
        for candidate in (clean + "\n", clean + "\t",
                          clean.replace("/article-", "/\narticle-"),
                          clean.replace("https://", "https://\t"),
                          clean + " ", clean + "\x7f"):
            with self.subTest(candidate=repr(candidate)):
                with self.assertRaises(ValueError):
                    og.canonical(candidate)

    def test_invalid_urls_and_untrusted_rss_rejected(self):
        for url in ("http://www.survival40.com/a/",
                    "https://www.survival40.com.evil.com/a/",
                    "https://www.survival40.com/a/?x=1",
                    "https://www.survival40.com/wp-admin/",
                    "https://www.survival40.com/a/#top"):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    og.canonical(url)
        feed = ET.parse(self.feed)
        items = feed.getroot().findall("./channel/item")
        items[1].find("link").text = items[0].findtext("link")
        feed.write(self.feed)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            og.source_items(self.feed)


if __name__ == "__main__":
    unittest.main()
