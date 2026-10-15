import datetime as dt
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

from PIL import Image
from scripts.pinterest import build_rss as m


def source(pid=512, date="2026-10-14T12:30:00", url="https://www.survival40.com/40s-eye-strain-massage-breaks/"):
    return {
        "id": pid, "status": "publish", "date_gmt": date, "link": url,
        "title": {"rendered": "40代男性の疲れ目をどうケアする？休憩の基本"},
        "excerpt": {"rendered": "<p>疲れ目を感じたとき、日常で見直したい休憩と生活習慣を整理します。</p>"},
        "content": {"rendered": "<p>広告なしの普通の記事</p>"},
    }


class PinterestRssTests(unittest.TestCase):
    def test_only_verified_claimed_origin_posts(self):
        self.assertEqual(m.verify(source())["id"], 512)
        for url in [
            "http://www.survival40.com/valid/",
            "https://survival40.com/valid/",
            "https://www.survival40.com.evil.test/valid/",
            "https://www.survival40.com/valid/?share=1",
            "https://www.survival40.com/valid/evil/",
        ]:
            self.assertIsNone(m.verify(source(url=url)), url)
        bad = source()
        bad["status"] = "draft"
        self.assertIsNone(m.verify(bad))
        bad = source()
        bad["id"] = "512"
        self.assertIsNone(m.verify(bad))

    def test_xml_is_valid_and_pinterest_image_tag_is_inside_item(self):
        posts = [m.verify(source()), m.verify(source(pid=900, date="2026-10-17T03:20:00", url="https://www.survival40.com/new-article/"))]
        raw = m.rss(posts)
        root = ET.fromstring(raw)
        self.assertEqual(root.attrib["version"], "2.0")
        items = root.findall("./channel/item")
        self.assertEqual(len(items), 2)
        for item in items:
            self.assertEqual(item.find("link").text.startswith(m.SITE + "/"), True)
            enclosure = item.find("enclosure")
            self.assertTrue(enclosure.attrib["url"].endswith(".png"))
            self.assertEqual(enclosure.attrib["type"], "image/png")
            self.assertEqual(item.find("guid").text, item.find("link").text)

    def test_cards_use_source_shiori_without_regenerating_or_overwriting(self):
        with tempfile.TemporaryDirectory() as tmp:
            portrait = Image.new("RGBA", (300, 400), (160, 0, 200, 255))
            p = m.verify(source())
            with patch.object(m, "ASSET_DIR", Path(tmp)):
                generated = m.render(p, portrait)
                self.assertEqual(Image.open(generated).size, (1000, 1500))
                before = generated.read_bytes()
                self.assertEqual(m.render(p, portrait).read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
