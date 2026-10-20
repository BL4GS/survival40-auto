"""Offline-only guarded one-for-one Shiori helpful note pilot tests."""
import datetime as dt
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

from ops.threads import useful_pilot_overlay as o
from scripts.threads.compose import validate_post
from scripts.threads.test_useful_preview import sample_feed

JST = ZoneInfo("Asia/Tokyo")
ORDINARY = "洗濯した服をたたみながら、どこにしまうか少し迷いました。"


class OverlayTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name)
        self.approved = base / "approved"
        src = self.approved / "scripts/threads"
        src.mkdir(parents=True)
        shutil.copyfile(Path("scripts/threads/useful_preview.py"),
                        src / "useful_preview.py")
        feed = self.approved / "pinterest/survival40-pins.xml"
        feed.parent.mkdir()
        feed.write_bytes(ET.tostring(sample_feed(), encoding="utf-8"))
        self.draft = base / "draft.json"
        self.now = dt.datetime(2026, 10, 22, 16, 5, tzinfo=JST)
        self.write_draft()

    def write_draft(self, when=None, **changes):
        now = when or self.now
        draft = {
            "id": now.date().isoformat() + "-afternoon",
            "date_jst": now.date().isoformat(),
            "slot": "afternoon",
            "account": "@survival40_jp",
            "kind": "everyday",
            "article_id": None, "article_url": None,
            "article_title": None,
            "text": ORDINARY,
            "publish": False,
            "status": "prepared_for_separate_publish_gate",
            "generated_at_jst": now.isoformat(timespec="seconds"),
        }
        draft.update(changes)
        self.draft.write_text(
            json.dumps(draft, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8"
        )
        return draft

    def apply(self, now=None):
        return o.apply(self.draft, self.approved, now or self.now, validate_post)

    def test_four_existing_thursday_slots_only_no_extra_posts(self):
        for idx, post_id in enumerate((608, 610, 616, 617)):
            today = self.now + dt.timedelta(weeks=idx)
            self.write_draft(today)
            status = self.apply(today)
            self.assertEqual(status, "PREPARED_ONE_FOR_ONE_HELPFUL_POST_NO_PUBLISH")
            result = json.loads(self.draft.read_text(encoding="utf-8"))
            self.assertEqual(result["id"], today.date().isoformat() + "-afternoon")
            self.assertEqual(result["helpful_source_post_id"], post_id)
            self.assertEqual(result["kind"], "everyday")
            self.assertIsNone(result["article_id"])
            self.assertFalse(result["publish"])
            self.assertEqual(result["status"], "prepared_for_separate_publish_gate")
            self.assertNotIn("https://", result["text"])
            self.assertEqual(validate_post(result["text"], "afternoon", 300),
                             result["text"])

    def test_outside_four_week_campaign_preserves_original_bytes(self):
        for when in (
            dt.datetime(2026, 10, 21, 16, 5, tzinfo=JST),
            dt.datetime(2026, 10, 22, 12, 5, tzinfo=JST),
            dt.datetime(2026, 11, 19, 16, 5, tzinfo=JST),
            dt.datetime(2026, 10, 23, 16, 5, tzinfo=JST),
        ):
            self.write_draft(when)
            before = self.draft.read_bytes()
            self.assertEqual(self.apply(when), "SKIPPED_NOT_APPROVED_SLOT")
            self.assertEqual(self.draft.read_bytes(), before)

    def test_article_calendar_slots_never_replaced(self):
        self.write_draft(kind="article", article_id=610,
                         article_url="https://www.survival40.com/a/",
                         article_title="記事")
        before = self.draft.read_bytes()
        self.assertEqual(self.apply(), "SKIPPED_NOT_APPROVED_SLOT")
        self.assertEqual(self.draft.read_bytes(), before)

    def test_wrong_account_unapproved_time_and_stale_timestamp_never_change(self):
        scenarios = (
            {"account": "@personal"},
            {"publish": True},
            {"generated_at_jst": "2026-10-21T16:05:00+09:00"},
            {"generated_at_jst": "2026-10-22T16:05:00Z"},
            {"status": "already_published"},
            {"article_id": 123},
        )
        for changes in scenarios:
            with self.subTest(changes=changes):
                self.write_draft(**changes)
                old = self.draft.read_bytes()
                self.assertEqual(self.apply(), "SKIPPED_NOT_APPROVED_SLOT")
                self.assertEqual(self.draft.read_bytes(), old)

    def test_missing_or_changed_article_excerpt_falls_back_to_everyday(self):
        path = self.approved / "pinterest/survival40-pins.xml"
        root = ET.fromstring(path.read_bytes())
        root.findall("./channel/item")[0].find("description").text = "内容不明"
        path.write_bytes(ET.tostring(root))
        old = self.draft.read_bytes()
        self.assertEqual(self.apply(), "SKIPPED_SOURCE_INVALID_ORDINARY_PRESERVED")
        self.assertEqual(self.draft.read_bytes(), old)

    def test_missing_second_article_must_not_shift_rotation(self):
        feed = self.approved / "pinterest/survival40-pins.xml"
        root = ET.fromstring(feed.read_bytes())
        channel = root.find("channel")
        channel.remove(channel.findall("item")[1])
        feed.write_bytes(ET.tostring(root))
        old = self.draft.read_bytes()
        self.assertEqual(self.apply(), "SKIPPED_SOURCE_INVALID_ORDINARY_PRESERVED")
        self.assertEqual(self.draft.read_bytes(), old)

    def test_missing_helper_or_rejected_copy_falls_back(self):
        helper = self.approved / "scripts/threads/useful_preview.py"
        helper.unlink()
        old = self.draft.read_bytes()
        self.assertEqual(self.apply(), "SKIPPED_SOURCE_INVALID_ORDINARY_PRESERVED")
        self.assertEqual(self.draft.read_bytes(), old)

    def test_validator_rejects_and_preserves_original(self):
        def reject(text, slot, limit):
            raise ValueError("unapproved")
        old = self.draft.read_bytes()
        self.assertEqual(
            o.apply(self.draft, self.approved, self.now, reject),
            "SKIPPED_SOURCE_INVALID_ORDINARY_PRESERVED",
        )
        self.assertEqual(self.draft.read_bytes(), old)

    def test_approved_snapshot_does_not_include_meta_posting(self):
        source = Path(o.__file__).read_text(encoding="utf-8")
        self.assertNotIn("MetaThreadsClient", source)
        self.assertNotIn("THREADS_ACCESS_TOKEN", source)
        self.assertNotIn("publish_text(", source)
        self.assertNotIn("reserve(", source)


if __name__ == "__main__":
    unittest.main()
