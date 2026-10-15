"""Guard against publishing malformed Pinterest RSS or mismatched Shiori images."""
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image
from scripts.pinterest import verify_static_feed as v
from scripts.pinterest.build_rss import RAW, SITE


class StaticFeedIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.asset_dir = root / "assets/pinterest/auto"
        self.asset_dir.mkdir(parents=True)
        self.png = self.asset_dir / "512.png"
        Image.new("RGB", (1000, 1500), (248, 248, 255)).save(self.png)
        self.rss_path = root / "pinterest/survival40-pins.xml"
        self.rss_path.parent.mkdir(parents=True)
        self.root = ET.Element("rss", {"version": "2.0"})
        ch = ET.SubElement(self.root, "channel")
        ET.SubElement(ch, "link").text = SITE + "/"
        self.item = ET.SubElement(ch, "item")
        ET.SubElement(self.item, "title").text = (
            "眼精疲労に目のマッサージは効く？40代男性の疲れ目対策と休憩のコツ")
        ET.SubElement(self.item, "description").text = (
            "40代男性の疲れ目対策と休憩について原典をもとに安全に整理。")
        article = SITE + "/40s-eye-strain-massage-breaks/"
        ET.SubElement(self.item, "link").text = article
        ET.SubElement(self.item, "guid", {"isPermaLink": "true"}).text = article
        ET.SubElement(self.item, "pubDate").text = "Tue, 13 Oct 2026 09:21:16 +0000"
        self.enc = ET.SubElement(self.item, "enclosure", {
            "url": RAW + "assets/pinterest/auto/512.png",
            "length": str(self.png.stat().st_size), "type": "image/png"})
        self.save()

    def save(self):
        self.rss_path.write_bytes(ET.tostring(self.root, encoding="utf-8"))

    def check(self):
        return v.validate(self.rss_path, self.asset_dir)

    def test_accepts_one_original_image_backed_claimed_article(self):
        self.assertEqual(self.check(), 1)

    def test_rejects_off_domain_or_duplicate_destinations(self):
        self.item.find("link").text = "https://evil.test/40s-eye-strain-massage-breaks/"
        self.save()
        with self.assertRaises(v.InvalidPinterestFeed):
            self.check()
        self.item.find("link").text = self.item.findtext("guid")
        self.root.find("channel").append(
            ET.fromstring(ET.tostring(self.item, encoding="utf-8")))
        self.save()
        with self.assertRaisesRegex(v.InvalidPinterestFeed, "Duplicate"):
            self.check()

    def test_rejects_missing_or_corrupt_images(self):
        self.png.unlink()
        with self.assertRaisesRegex(v.InvalidPinterestFeed, "missing"):
            self.check()
        self.png.write_bytes(b"not an image")
        self.enc.set("length", str(self.png.stat().st_size))
        self.save()
        with self.assertRaises(v.InvalidPinterestFeed):
            self.check()

    def test_rejects_unsupported_card_shape(self):
        Image.new("RGB", (1000, 1000), (248, 248, 255)).save(self.png)
        self.enc.set("length", str(self.png.stat().st_size))
        self.save()
        with self.assertRaisesRegex(v.InvalidPinterestFeed, "2:3"):
            self.check()

    def test_rejects_extra_media_and_wrong_card_metadata(self):
        ET.SubElement(self.item, "{http://search.yahoo.com/mrss/}content",
                      {"url": "https://example.test/banner.png"})
        self.save()
        with self.assertRaisesRegex(v.InvalidPinterestFeed, "Unexpected item tag"):
            self.check()
        self.item.remove(self.item[-1])
        self.enc.set("length", "123")
        self.save()
        with self.assertRaisesRegex(v.InvalidPinterestFeed, "length"):
            self.check()

    def test_rejects_metricool_pin_393_duplication(self):
        self.enc.set("url", RAW + "assets/pinterest/auto/393.png")
        self.save()
        with self.assertRaisesRegex(v.InvalidPinterestFeed, "duplicate"):
            self.check()


if __name__ == "__main__":
    unittest.main()
