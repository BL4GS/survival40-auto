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
