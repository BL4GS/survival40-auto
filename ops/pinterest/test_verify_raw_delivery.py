"""Offline, no-network tests for the pre-existing Pinterest native RSS transport."""
import hashlib
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from ops.pinterest import verify_raw_delivery as p


def rss(article_id=512, target="https://www.survival40.com/40s-eye-strain-massage-breaks/"):
    root = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(root, "channel")
    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = "40代男性の疲れ目と休憩"
    ET.SubElement(item, "description").text = "眼精疲労についての実用的な公開記事"
    ET.SubElement(item, "link").text = target
    ET.SubElement(item, "guid").text = target
    ET.SubElement(item, "enclosure", {
        "url": p.PIN_URL_ROOT + str(article_id) + ".png",
        "type": "image/png", "length": "4"
    })
    return ET.tostring(root, encoding="utf-8")


class PublicFeedDeliveryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.feed = root / "feed.xml"
        self.pins = root / "pins"
        self.report = root / "proof.json"
        self.pins.mkdir()
        self.feed.write_bytes(rss())
        self.image = b"\x89PNG\r\n\x1a\n123456789"
        (self.pins / "512.png").write_bytes(self.image)
        self.calls = []

    def fetch(self, url, maximum):
        self.calls.append((url, maximum))
        if url == p.FEED_URL:
            return self.feed.read_bytes(), "text/plain"
        if url == p.PIN_URL_ROOT + "512.png":
            return self.image, "image/png"
        raise AssertionError("Attempted unexpected source")

    def call(self, fetch=None):
        return p.probe(self.feed, self.pins, self.report, fetch or self.fetch)

    def test_transport_verifies_exact_repo_bytes_not_pin_publication(self):
        result = self.call()
        self.assertEqual(result["status"], "RSS_AND_SAMPLE_IMAGE_TRANSPORT_OK")
        self.assertTrue(result["remote_rss_byte_identical"])
        self.assertTrue(result["remote_image_sha256_matches_local"])
        self.assertFalse(result["published_pinterest_pin_verified"])
        self.assertFalse(result["pinterest_rss_subscription_verified_by_this_probe"])
        self.assertFalse(result["website_sessions_verified"])
        self.assertEqual(result["network_get_budget"], 2)
        self.assertEqual(len(self.calls), 2)
        self.assertTrue(self.report.is_file())

    def test_remote_xml_difference_is_not_called_pinterest_failure(self):
        def altered(url, maximum):
            self.calls.append((url, maximum))
            return b"<rss>changed</rss>", "text/plain"
        result = self.call(altered)
        self.assertEqual(result["status"], "REMOTE_RSS_DIFFERS_REVIEW_CACHE_OR_UPDATE")
        self.assertFalse(result["remote_rss_byte_identical"])
        self.assertEqual(len(self.calls), 1)
        self.assertFalse(result["published_pinterest_pin_verified"])

    def test_bad_remote_image_requires_review(self):
        def mismatched(url, maximum):
            self.calls.append((url, maximum))
            if url == p.FEED_URL:
                return self.feed.read_bytes(), "text/plain"
            return b"different image", "image/png"
        result = self.call(mismatched)
        self.assertEqual(result["status"], "REMOTE_IMAGE_DIFFERS_REVIEW")
        self.assertFalse(result["remote_image_sha256_matches_local"])

    def test_source_down_is_unknown_not_zero_pins(self):
        def down(url, maximum):
            raise p.TransportCheckError("Unavailable")
        result = self.call(down)
        self.assertEqual(result["status"], "UNAVAILABLE_UNVERIFIED")
        self.assertEqual(result["error_type"], "TransportCheckError")
        self.assertFalse(result["published_pinterest_pin_verified"])

    def test_offdomain_pins_and_articles_rejected(self):
        cases = [
            rss(target="https://evil.test/marketing/"),
            rss(target="https://www.survival40.com.evil.test/p/"),
            rss(target="https://www.survival40.com/ok/?tracking=1"),
            rss(article_id=0),
        ]
        for content in cases:
            with self.subTest(content=content), self.assertRaises(p.TransportCheckError):
                p.local_article_media_pairs(content)

    def test_duplicate_articles_rejected(self):
        root = ET.fromstring(rss())
        channel = root.find("channel")
        duplicate = ET.fromstring(ET.tostring(channel.find("item")))
        channel.append(duplicate)
        with self.assertRaises(p.TransportCheckError):
            p.local_article_media_pairs(ET.tostring(root))

    def test_image_fetch_cannot_target_any_other_host(self):
        for url in (
            "https://evil.test/pin.png",
            p.PIN_URL_ROOT + "512.png?track=yes",
            p.PIN_URL_ROOT + "../../secrets",
            "http://raw.githubusercontent.com/BL4GS/survival40-auto/main/"
            "assets/pinterest/auto/512.png",
        ):
            with self.subTest(url=url), self.assertRaises(p.TransportCheckError):
                p.get_bytes(url, p.MAX_IMAGE)

    def test_invalid_xml_and_empty_items_are_rejected(self):
        for content in (b"<rss>", b"<rss version='2.0'><channel/></rss>",
                        b"<feed></feed>"):
            with self.subTest(content=content), self.assertRaises(p.TransportCheckError):
                p.local_article_media_pairs(content)

    def test_no_publishing_or_credentials_in_module(self):
        source = Path(p.__file__).read_text(encoding="utf-8")
        self.assertNotIn("THREADS_ACCESS_TOKEN", source)
        self.assertNotIn("PIN_ACCESS_TOKEN", source)
        self.assertNotIn("GITHUB_TOKEN", source)
        self.assertNotIn("POST(", source)
        self.assertFalse(self.call()["published_pinterest_pin_verified"])


if __name__ == "__main__":
    unittest.main()
