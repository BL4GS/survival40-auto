"""Credential-free tests: helpful Threads samples cannot publish or invent sources."""
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch

from scripts.threads import useful_preview as preview


def sample_feed():
    root = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(root, "channel")
    values = {
        608: ("40代男性の服のサイズ選び｜肩幅・身幅・着丈の測り方",
              "肩幅・身幅・着丈を確認して返品条件も確認する"),
        610: ("洗濯した服のニオイが気になる",
              "洗剤量・詰め込み・乾燥・洗濯槽の確認点"),
        616: ("40代男性の私服は何着必要",
              "週末の外出回数・洗濯頻度・季節を考えて棚卸し"),
        617: ("40代男性の靴が臭い原因と対策",
              "足の洗い方、靴下の交換、靴の乾燥を確認"),
    }
    for rule in preview.RULES:
        entry = ET.SubElement(channel, "item")
        title, description = values[rule["id"]]
        ET.SubElement(entry, "title").text = title
        ET.SubElement(entry, "description").text = description
        ET.SubElement(entry, "link").text = (
            preview.SITE + "/" + rule["slug"] + "/"
        )
        ET.SubElement(entry, "enclosure", {
            "url": preview.IMG_ROOT + str(rule["id"]) + ".png",
            "type": "image/png",
        })
    return root


class UsefulPreviewTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.feed = Path(tmp.name) / "rss.xml"
        self.feed.write_bytes(ET.tostring(sample_feed(), encoding="utf-8"))

    def test_all_four_grounded_samples_never_marked_for_publish(self):
        actual = preview.make_previews(preview.verified_articles(self.feed))
        self.assertEqual(len(actual), 4)
        self.assertEqual({p["source_post_id"] for p in actual}, {608, 610, 616, 617})
        for candidate in actual:
            self.assertFalse(candidate["publish"])
            self.assertEqual(candidate["status"], "REVIEW_PREVIEW_ONLY")
            self.assertTrue(candidate["requires_live_post_recheck"])
            self.assertEqual(candidate["account"], "@survival40_jp")
            self.assertNotIn("https://", candidate["text"])
            self.assertLessEqual(len(candidate["text"]), 240)

    def test_one_source_excerpt_missing_refuses_invention(self):
        root = sample_feed()
        root.findall("./channel/item")[0].find("description").text = (
            "内容が書かれていない紹介文"
        )
        self.feed.write_bytes(ET.tostring(root, encoding="utf-8"))
        with self.assertRaisesRegex(preview.PreviewSourceError, "identity"):
            preview.verified_articles(self.feed)

    def test_wrong_original_artwork_identity_is_not_accepted(self):
        root = sample_feed()
        root.findall("./channel/item")[1].find("enclosure").set(
            "url", preview.IMG_ROOT + "999.png"
        )
        self.feed.write_bytes(ET.tostring(root, encoding="utf-8"))
        with self.assertRaisesRegex(preview.PreviewSourceError, "identity"):
            preview.verified_articles(self.feed)

    def test_no_unapproved_article_leaks_into_preview(self):
        root = sample_feed()
        e = ET.SubElement(root.find("channel"), "item")
        ET.SubElement(e, "link").text = "https://evil.test/promo/"
        ET.SubElement(e, "title").text = "買ってよかった"
        ET.SubElement(e, "description").text = "宣伝"
        self.feed.write_bytes(ET.tostring(root, encoding="utf-8"))
        actual = preview.make_previews(preview.verified_articles(self.feed))
        self.assertEqual(len(actual), 4)
        self.assertNotIn("evil.test", json.dumps(actual))

    def test_duplicate_url_rejected(self):
        root = sample_feed()
        links = root.findall("./channel/item/link")
        links[1].text = links[0].text
        self.feed.write_bytes(ET.tostring(root, encoding="utf-8"))
        with self.assertRaisesRegex(preview.PreviewSourceError, "Duplicate"):
            preview.verified_articles(self.feed)

    def test_invalid_feed_and_large_feed_rejected(self):
        self.feed.write_text("<rss>")
        with self.assertRaises(preview.PreviewSourceError):
            preview.verified_articles(self.feed)
        self.feed.write_bytes(b"x" * (preview.MAX_FEED_BYTES + 1))
        with self.assertRaisesRegex(preview.PreviewSourceError, "safe size"):
            preview.verified_articles(self.feed)

    def test_missing_target_article_does_not_generate_it(self):
        root = sample_feed()
        root.find("channel").remove(root.findall("./channel/item")[2])
        self.feed.write_bytes(ET.tostring(root, encoding="utf-8"))
        actual = preview.make_previews(preview.verified_articles(self.feed))
        self.assertEqual(len(actual), 3)
        self.assertFalse(any(x["source_post_id"] == 616 for x in actual))

    def test_every_sample_is_under_persona_and_copy_limit(self):
        candidates = preview.make_previews(preview.verified_articles(self.feed))
        for c in candidates:
            text = c["text"]
            self.assertTrue(text.endswith("。") or text.endswith("ね。"))
            self.assertFalse(any(bad in text for bad in (
                "彼氏", "夫", "息子", "私は試した", "治ります", "【PR】"
            )))

    def test_no_meta_credentials_or_network_used_by_main(self):
        import scripts.threads.useful_preview as u
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "sample.json"
            with (patch.object(u, "FEED", self.feed),
                  patch.object(u, "OUTPUT", output),
                  patch("urllib.request.urlopen") as network):
                u.main()
                network.assert_not_called()
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertFalse(data["publish"])
            self.assertEqual(data["mode"], "preview_only_no_meta_credentials")
            self.assertTrue(data[
                "requires_fresh_wordpress_verification_before_any_later_live_use"
            ])
            self.assertEqual(len(data["posts"]), 4)


    def test_main_respects_configured_feed_when_one_approved_source_is_absent(self):
        # Regression: the old default argument captured the production FEED at
        # import time, ignoring the patched feed passed to main() in tests.
        root = sample_feed()
        root.find("channel").remove(root.findall("./channel/item")[0])
        self.feed.write_bytes(ET.tostring(root, encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "sample.json"
            with (patch.object(preview, "FEED", self.feed),
                  patch.object(preview, "OUTPUT", output),
                  patch("urllib.request.urlopen") as network):
                preview.main()
                network.assert_not_called()
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                {p["source_post_id"] for p in data["posts"]},
                {610, 616, 617},
            )
            self.assertFalse(data["publish"])


if __name__ == "__main__":
    unittest.main()
