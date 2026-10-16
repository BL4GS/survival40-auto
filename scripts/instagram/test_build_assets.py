"""Offline tests for shared Shiori Instagram/OG cards and no-post manifest."""
import datetime as dt
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from scripts.instagram import build_assets as m
from scripts.pinterest import build_rss as p


class InstagramAssetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.pin_dir = root / "assets/pinterest/auto"
        self.ig_dir = root / "assets/instagram/auto"
        self.og_dir = root / "assets/social/og"
        self.xml = root / "pinterest/survival40-pins.xml"
        self.manifest = root / "instagram/ready-posts.json"
        self.pin_dir.mkdir(parents=True)
        self.xml.parent.mkdir(parents=True)
        self.portrait = Image.new("RGBA", (300, 420), (0, 0, 0, 0))
        Image.new("RGB", (240, 360), "#D2A9A4").save(root / "test-art.png")
        self.portrait.paste((99, 50, 100, 255), (50, 60, 250, 390))
        self.add_post(512, "眼精疲労に目のマッサージは効く？40代男性の疲れ目対策と休憩のコツ")
        self.add_post(516, "女性は男性の身だしなみのどこを見る？調査でわかる清潔感とヒゲ・髪・体臭")

    def add_post(self, ident, title):
        img = self.pin_dir / f"{ident}.png"
        Image.new("RGB", (1000, 1500), "#F8F8FF").save(img)
        if self.xml.exists():
            root = ET.parse(self.xml).getroot()
        else:
            root = ET.Element("rss", {"version": "2.0"})
            ch = ET.SubElement(root, "channel")
            ET.SubElement(ch, "link").text = p.SITE + "/"
        ch = root.find("channel")
        item = ET.SubElement(ch, "item")
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = p.SITE + f"/topic-{ident}/"
        ET.SubElement(item, "guid", {"isPermaLink": "true"}).text = p.SITE + f"/topic-{ident}/"
        ET.SubElement(item, "description").text = (
            "40代男性向けに役立つポイントと注意点をわかりやすく整理します。")
        ET.SubElement(item, "pubDate").text = "Tue, 13 Oct 2026 09:21:16 +0000"
        ET.SubElement(item, "enclosure", {
            "url": p.RAW + f"assets/pinterest/auto/{ident}.png",
            "length": str(img.stat().st_size), "type": "image/png"})
        self.xml.write_bytes(ET.tostring(root, encoding="utf-8"))

    def build(self):
        return m.build(self.xml, self.pin_dir, portrait=self.portrait,
                       instagram_dir=self.ig_dir, og_dir=self.og_dir,
                       manifest_path=self.manifest)

    def test_renders_both_orientations_and_review_only_manifest(self):
        manifest = self.build()
        self.assertFalse(manifest["publishing_enabled"])
        self.assertEqual([x["article_id"] for x in manifest["items"]], [512, 516])
        for item in manifest["items"]:
            ident = item["article_id"]
            self.assertEqual(item["status"], "assets_ready_not_published")
            self.assertIn("Survival40", item["caption_draft"])
            self.assertNotIn("プロフィールのリンク", item["caption_draft"])
            self.assertTrue(item["article_url"].startswith(p.SITE + "/"))
            self.assertEqual(
                item["instagram_image"],
                p.RAW + f"assets/instagram/auto/{ident}.png")
            self.assertEqual(
                item["social_og_image"],
                p.RAW + f"assets/social/og/{ident}.png")
            for dest, size in [(self.ig_dir, m.IG_SIZE), (self.og_dir, m.OG_SIZE)]:
                with Image.open(dest / f"{ident}.png") as image:
                    self.assertEqual(image.size, size)
                    self.assertEqual(image.getpixel((0, 0)), (248, 248, 255))
        saved = self.manifest.read_bytes()
        self.assertEqual(self.build(), manifest)
        self.assertEqual(self.manifest.read_bytes(), saved)

    def test_refuses_missing_pin_art_without_ig_output(self):
        (self.pin_dir / "516.png").unlink()
        with self.assertRaisesRegex(ValueError, "missing"):
            self.build()
        self.assertFalse(self.ig_dir.exists())
        self.assertFalse(self.manifest.exists())

    def test_previously_prepared_images_not_overwritten(self):
        self.build()
        img = self.ig_dir / "512.png"
        previous = img.read_bytes()
        with patch.object(m, "BG", "#000000"):
            self.build()
        self.assertEqual(img.read_bytes(), previous)

    def test_no_remote_fetch_when_portrait_provided(self):
        with patch.object(p, "request_bytes", side_effect=RuntimeError("No network")):
            self.build()


if __name__ == "__main__":
    unittest.main()
