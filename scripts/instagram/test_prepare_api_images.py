"""Offline tests: native Instagram JPEG media preparation never publishes."""
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from scripts.instagram import prepare_api_images as m


class InstagramApiMediaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.pngs = root / "png"
        self.jpgs = root / "jpg"
        self.manifest = root / "input.json"
        self.output = root / "output.json"
        self.pngs.mkdir(parents=True)
        Image.new("RGB", (1080, 1350), "#F8F8FF").save(self.pngs / "518.png")
        self.data = {
            "brand": "Survival40",
            "source": "verified_Pinterest_static_feed",
            "publishing_enabled": False,
            "items": [{
                "article_id": 518,
                "article_url": "https://www.survival40.com/test-native-instagram/",
                "instagram_image": m.PNG_PREFIX + "518.png",
                "caption_draft": "【PR】\n具体的な説明。\n\n詳しくはプロフィールのリンクからSurvival40へ。",
                "status": "assets_ready_not_published",
            }],
        }
        self.save()

    def save(self):
        self.manifest.write_text(json.dumps(self.data, ensure_ascii=False),
                                 encoding="utf-8")

    def build(self):
        return m.build(self.manifest, self.pngs, self.jpgs, self.output)

    def test_generates_stable_jpeg_without_publish_tokens(self):
        manifest = self.build()
        self.assertFalse(manifest["publishing_enabled"])
        self.assertFalse(manifest["official_instagram_api_enabled"])
        self.assertEqual(manifest["items"][0]["article_id"], 518)
        self.assertEqual(manifest["items"][0]["status"], "MEDIA_ONLY_NOT_PUBLISHED")
        self.assertEqual(manifest["items"][0]["public_jpeg_url"], m.JPG_PREFIX + "518.jpg")
        self.assertNotIn("access_token", json.dumps(manifest))
        with Image.open(self.jpgs / "518.jpg") as img:
            self.assertEqual(img.format, "JPEG")
            self.assertEqual(img.size, (1080, 1350))
        saved = self.output.read_bytes()
        self.assertEqual(self.build(), manifest)
        self.assertEqual(self.output.read_bytes(), saved)

    def test_fails_on_wrong_image_dimensions(self):
        Image.new("RGB", (1024, 1024)).save(self.pngs / "518.png")
        with self.assertRaisesRegex(ValueError, "1080x1350"):
            self.build()
        self.assertFalse(self.output.exists())

    def test_fails_on_unknown_url(self):
        self.data["items"][0]["article_url"] = "https://example.net/hijack/"
        self.save()
        with self.assertRaisesRegex(ValueError, "canonical"):
            self.build()

    def test_fails_on_manipulated_image_id(self):
        self.data["items"][0]["instagram_image"] = m.PNG_PREFIX + "999.png"
        self.save()
        with self.assertRaisesRegex(ValueError, "mismatch"):
            self.build()

    def test_rejects_manifest_with_publishing_enabled(self):
        self.data["publishing_enabled"] = True
        self.save()
        with self.assertRaisesRegex(ValueError, "Unverified"):
            self.build()

    def test_rejects_duplicate_article_ids(self):
        self.data["items"].append(dict(self.data["items"][0]))
        self.save()
        with self.assertRaisesRegex(ValueError, "repeated"):
            self.build()


if __name__ == "__main__":
    unittest.main()
