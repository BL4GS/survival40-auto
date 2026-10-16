"""Offline fail-closed tests for non-publishing Instagram candidate queue."""
import datetime as dt
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

from scripts.instagram import build_assets as cards
from scripts.instagram import prepare_queue as q


class VerifiedInstagramQueueTests(unittest.TestCase):
    def setUp(self):
        self.root_tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.root_tmp.cleanup)
        root = Path(self.root_tmp.name)
        self.feed = root / "pinterest" / "feed.xml"
        self.ready = root / "instagram" / "ready-posts.json"
        self.output = root / "instagram" / "publish-queue.json"
        self.images = root / "assets" / "instagram" / "auto"
        self.images.mkdir(parents=True)
        self.feed.parent.mkdir(parents=True)
        self.ready.parent.mkdir(parents=True)
        self.posts = []
        self.entries = []
        self.feed_items = [
            (512, "2026-10-13T09:21:16+00:00"),
            (516, "2026-10-15T22:00:00+00:00"),
            (518, "2026-10-16T12:00:00+00:00"),
        ]
        self.make_data()

    def make_data(self):
        root = ET.Element("rss", {"version": "2.0"})
        channel = ET.SubElement(root, "channel")
        self.posts, self.entries = [], []
        for ident, date in self.feed_items:
            title = f"40代男性の身だしなみについて確認したいこと {ident}"
            url = f"https://www.survival40.com/article-{ident}/"
            desc = "何を先に調べるべきか？確認の手順と根拠の扱いを、わかりやすく整理します。"
            post = {"id": ident, "title": title, "article_url": url, "excerpt": desc}
            self.posts.append(post)
            item = ET.SubElement(channel, "item")
            ET.SubElement(item, "title").text = title
            ET.SubElement(item, "link").text = url
            ET.SubElement(item, "pubDate").text = (
                dt.datetime.fromisoformat(date).strftime("%a, %d %b %Y %H:%M:%S %z"))
            ET.SubElement(item, "enclosure", {
                "url": cards.PIN_PREFIX + str(ident) + ".png",
                "length": "300",
                "type": "image/png",
            })
            self.entries.append({
                "article_id": ident, "title": title, "article_url": url,
                "caption_draft": cards.caption_from_source(post),
                "instagram_image": q.RAW_PREFIX + str(ident) + ".png",
                "status": "assets_ready_not_published",
            })
            Image.new("RGB", cards.IG_SIZE, "#F8F8FF").save(
                self.images / (str(ident) + ".png"))
        self.feed.write_bytes(ET.tostring(root, encoding="utf-8"))
        self.save_manifest()

    def save_manifest(self):
        self.ready.write_text(json.dumps({
            "brand": "Survival40", "source": "verified_Pinterest_static_feed",
            "publishing_enabled": False, "items": self.entries,
        }, ensure_ascii=False), encoding="utf-8")

    def prepare(self):
        return q.prepare(self.feed, self.ready, self.images, self.output,
                         trusted_posts=self.posts)

    def test_exact_new_article_only_and_non_publishing(self):
        out = self.prepare()
        self.assertFalse(out["publishing_enabled"])
        self.assertFalse(out["pilot_success_verified"])
        self.assertEqual([x["article_id"] for x in out["items"]], [518])
        self.assertEqual(out["items"][0]["status"],
                         "NOT_SCHEDULED_REQUIRES_METRICOOL_CHECK")
        self.assertNotIn("autoPublish", json.dumps(out))
        self.assertNotIn("access_token", json.dumps(out))
        previous = self.output.read_bytes()
        self.assertEqual(self.prepare(), out)
        self.assertEqual(self.output.read_bytes(), previous)

    def test_excludes_old_articles_and_first_scheduled_pilot(self):
        self.feed_items = self.feed_items[:2]
        self.make_data()
        self.assertEqual(self.prepare()["items"], [])

    def test_rejects_tampered_target_and_never_writes_queue(self):
        self.entries[-1]["article_url"] = "https://attacker.example/article-518/"
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, "does not match"):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_rejects_wrong_public_png(self):
        Image.new("RGB", (700, 700)).save(self.images / "518.png")
        with self.assertRaisesRegex(ValueError, "1080x1350"):
            self.prepare()

    def test_rejects_missing_image(self):
        (self.images / "518.png").unlink()
        with self.assertRaisesRegex(ValueError, "Missing original"):
            self.prepare()

    def test_rejects_failed_verified_feed_contract(self):
        self.entries[-1]["caption_draft"] = "【PR】使ってみた！"
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, "does not match"):
            self.prepare()

    def test_rejects_duplicate_feed_urls(self):
        self.posts[-1]["article_url"] = self.posts[-2]["article_url"]
        # Change feed link directly; both URLs will collide.
        root = ET.parse(self.feed).getroot()
        items = root.findall("./channel/item")
        items[-1].find("link").text = items[-2].findtext("link")
        self.feed.write_bytes(ET.tostring(root, encoding="utf-8"))
        with self.assertRaisesRegex(ValueError, "Duplicated"):
            self.prepare()

    def test_rejects_unknown_manifest_entry(self):
        self.entries.append(dict(self.entries[-1], article_id=999))
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, "Untrusted"):
            self.prepare()


if __name__ == "__main__":
    unittest.main()
