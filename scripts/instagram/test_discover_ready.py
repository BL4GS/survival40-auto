"""Offline regression tests for original article OG image readiness."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

from scripts.instagram import build_assets as cards
from scripts.instagram import discover_ready as d


class DiscoverAssetsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.ig = root / "assets/instagram/auto"
        self.og = root / "assets/social/og"
        self.ready = root / "instagram/ready-posts.json"
        self.report = root / "out/result.json"
        self.ig.mkdir(parents=True)
        self.og.mkdir(parents=True)
        self.ready.parent.mkdir(parents=True)
        self.posts = [
            {"id": 608, "title": "40代男性の通販で服のサイズを確認する方法",
             "excerpt": "肩幅や身幅と着丈を見て、返品できるかを確かめます。",
             "article_url": "https://www.survival40.com/test-article-608/"},
            {"id": 610, "title": "洗濯しても服にニオイが残るときの対策",
             "excerpt": "洗剤の量と衣類の詰め込みすぎを先に点検してみます。",
             "article_url": "https://www.survival40.com/test-article-610/"},
        ]
        self.entries = []
        for post in self.posts:
            ident = post["id"]
            Image.new("RGB", cards.IG_SIZE, "#eeeeee").save(
                self.ig / f"{ident}.png")
            Image.new("RGB", cards.OG_SIZE, "#eeeeee").save(
                self.og / f"{ident}.png")
            self.entries.append({
                "article_id": ident, "title": post["title"],
                "article_url": post["article_url"],
                "caption_draft": cards.caption_from_source(post),
                "instagram_image": d.RAW + f"assets/instagram/auto/{ident}.png",
                "social_og_image": d.RAW + f"assets/social/og/{ident}.png",
                "status": "assets_ready_not_published",
            })
        self.write_manifest()

    def write_manifest(self, flag=False):
        self.ready.write_text(json.dumps({
            "brand": "Survival40",
            "source": "verified_Pinterest_static_feed",
            "publishing_enabled": flag,
            "items": self.entries,
        }, ensure_ascii=False), encoding="utf-8")

    def verify(self):
        return d.verify(
            ready=self.ready, ig=self.ig, og=self.og, report=self.report,
            trusted_posts=self.posts,
        )

    def test_all_pairs_fully_decode_and_remain_candidates(self):
        with patch("urllib.request.urlopen") as remote:
            result = self.verify()
            remote.assert_not_called()
        self.assertEqual(result["article_count"], 2)
        self.assertTrue(result["all_candidate_images_decode_1200x630"])
        self.assertTrue(result["read_only"])
        self.assertFalse(result["changed_wordpress"])
        self.assertFalse(result["published_to_social"])
        for row in result["items"]:
            self.assertEqual(row["proposed_social_og_image_proof"]["width"], 1200)
            self.assertEqual(row["proposed_social_og_image_proof"]["height"], 630)
            self.assertEqual(row["existing_instagram_image_proof"]["width"], 1080)
            self.assertEqual(row["existing_instagram_image_proof"]["height"], 1350)
            self.assertEqual(len(row["proposed_social_og_image_proof"]["sha256"]), 64)
            self.assertIsNone(row["wordpress_og_image_matches_candidate"])
            self.assertFalse(row["discover_eligibility_verified"])
            self.assertFalse(row["live_image_url_fetch_verified"])
        self.assertTrue(self.report.is_file())

    def test_rejects_mismatched_og_image_size(self):
        Image.new("RGB", cards.IG_SIZE).save(self.og / "608.png")
        with self.assertRaisesRegex(ValueError, "dimensions mismatch"):
            self.verify()
        self.assertFalse(self.report.exists())

    def test_rejects_truncated_or_non_image(self):
        (self.og / "610.png").write_bytes(b"not a real image" * 20)
        with self.assertRaisesRegex(ValueError, "decoded"):
            self.verify()
        self.assertFalse(self.report.exists())

    def test_refuses_wrong_article_image_url(self):
        self.entries[0]["social_og_image"] = (
            d.RAW + "assets/social/og/610.png")
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "mapping"):
            self.verify()

    def test_refuses_external_or_fake_canonical_destination(self):
        self.entries[0]["article_url"] = "https://evil.test/promoted/"
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "mapping"):
            self.verify()

    def test_refuses_duplicate_ids_and_missing_manifest_entries(self):
        self.entries.append(dict(self.entries[0]))
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.verify()
        self.entries = [self.entries[0]]
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "does not cover"):
            self.verify()

    def test_refuses_publish_enabled_or_unverified_manifest(self):
        self.write_manifest(flag=True)
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            self.verify()
        self.write_manifest()
        self.entries[0]["status"] = "published"
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "mapping"):
            self.verify()

    def test_refuses_forged_caption_and_missing_image(self):
        self.entries[0]["caption_draft"] = "使ってみて最高でした。"
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "mapping"):
            self.verify()
        self.entries[0]["caption_draft"] = cards.caption_from_source(self.posts[0])
        self.write_manifest()
        (self.og / "608.png").unlink()
        with self.assertRaisesRegex(ValueError, "Missing"):
            self.verify()

    def test_refuses_untrusted_and_oversized_inventory(self):
        with self.assertRaisesRegex(ValueError, "inventory"):
            d.verify(ready=self.ready, ig=self.ig, og=self.og,
                     report=self.report, trusted_posts=[])
        many = [dict(self.posts[0], id=i) for i in range(1, 100)]
        with self.assertRaisesRegex(ValueError, "inventory"):
            d.verify(ready=self.ready, ig=self.ig, og=self.og,
                     report=self.report, trusted_posts=many)


if __name__ == "__main__":
    unittest.main()
