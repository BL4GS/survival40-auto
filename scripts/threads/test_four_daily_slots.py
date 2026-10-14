"""No-token regression tests for the 08/12/16/20 Shiori daily schedule."""
import datetime as dt
import json
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from scripts.threads.compose import (
    CONFIG, SLOTS, SLOT_HOURS, build_prompt, choose_slot,
    select_editorial_topic, validate_post,
)
from scripts.threads.prepare_schedule import choose_copy, MORNING_GREETING, ARTICLE_CALENDAR
from scripts.threads.scheduled_publisher import verify_draft
from scripts.threads.ledger import GithubLedger

JST = ZoneInfo("Asia/Tokyo")
ORDINARY = "机の上に置いた日用品を片づけようと思っていたのに、気がつくと別のことを始めていました。"


def at(day=15, hour=12, minute=5):
    return dt.datetime(2026, 10, day, hour, minute, tzinfo=JST)


class FourDailySlotsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))

    def test_exact_four_hour_windows_and_no_accidental_posting(self):
        self.assertEqual(SLOT_HOURS, {"morning": 8, "midday": 12, "afternoon": 16, "evening": 20})
        self.assertEqual(SLOTS, ("morning", "midday", "afternoon", "evening"))
        for name, hour in SLOT_HOURS.items():
            self.assertEqual(choose_slot(at(hour=hour, minute=0)), name)
            self.assertEqual(choose_slot(at(hour=hour, minute=59)), name)
            self.assertIsNone(choose_slot(at(hour=hour-1, minute=59)))
        self.assertIsNone(choose_slot(at(hour=22)))
        self.assertIsNone(choose_slot(at(hour=23)))
        for hour in (9, 11, 13, 15, 17, 19, 21):
            self.assertIsNone(choose_slot(at(hour=hour)))

    def test_new_noon_afternoon_have_new_durable_ledger_keys(self):
        self.assertEqual(GithubLedger.filename("2026-10-15-midday"),
                         "threads-ledger/2026/10/2026-10-15-midday.json")
        self.assertEqual(GithubLedger.filename("2026-10-15-afternoon"),
                         "threads-ledger/2026/10/2026-10-15-afternoon.json")
        self.assertNotEqual(GithubLedger.filename("2026-10-15-midday"),
                            GithubLedger.filename("2026-10-15-evening"))
        for invalid in ("2026-10-15-noon", "2026-10-15-22", "2026-10-15-all"):
            with self.assertRaises(ValueError):
                GithubLedger.filename(invalid)

    def test_drafts_of_new_slots_keep_persona_not_promotional(self):
        for slot, hour in (("midday", 12), ("afternoon", 16)):
            with self.subTest(slot=slot), patch(
                "scripts.threads.prepare_schedule.gemini_generate", return_value=ORDINARY
            ) as gemini:
                date = at(hour=hour)
                draft = choose_copy(date, self.config, "FAKE_GEMINI")
                self.assertEqual(draft["slot"], slot)
                self.assertEqual(draft["id"], date.date().isoformat() + "-" + slot)
                self.assertEqual(draft["kind"], "everyday")
                self.assertIsNone(draft["article_id"])
                self.assertIsNone(draft["article_url"])
                self.assertEqual(draft["text"], ORDINARY)
                self.assertNotIn("PR", draft["text"])
                self.assertEqual(verify_draft(draft, date, self.config), ORDINARY)
                gemini.assert_called_once()

    def test_08_greeting_and_20_special_introductions_unchanged(self):
        with patch("scripts.threads.prepare_schedule.gemini_generate", return_value=ORDINARY):
            draft = choose_copy(at(hour=8), self.config, "FAKE_GEMINI")
        self.assertTrue(draft["text"].startswith(MORNING_GREETING + "\n"))
        self.assertEqual(verify_draft(draft, at(hour=8), self.config), draft["text"])
        at20 = at(day=17, hour=20)
        self.assertIn(at20.date().isoformat(), ARTICLE_CALENDAR)
        article = choose_copy(at20, self.config, None)
        self.assertEqual(article["kind"], "article")
        self.assertIn("/40s-male-yoga-mat-home-training/", article["text"])
        self.assertEqual(verify_draft(article, at20, self.config), article["text"])
        self.assertIsNone(choose_copy(at(day=17, hour=22), self.config, "FAKE_GEMINI"))

    def test_bogus_slot_timestamp_and_html_blocked(self):
        with patch("scripts.threads.prepare_schedule.gemini_generate", return_value=ORDINARY):
            draft = choose_copy(at(), self.config, "FAKE_GEMINI")
        for patch_fields in (
            {"slot": "evening"},
            {"id": "2026-10-15-evening"},
            {"date_jst": "2026-10-14"},
            {"text": "この記事を買ってください https://example.com"},
            {"generated_at_jst": "2026-10-15T12:50:00+09:00"},
        ):
            with self.subTest(patch_fields=patch_fields), self.assertRaises(ValueError):
                verify_draft(dict(draft, **patch_fields), at(), self.config)
        with self.assertRaises(ValueError):
            verify_draft(draft, at(hour=16), self.config)

    def test_more_posts_do_not_change_existing_original_topic_sequence(self):
        for day in range(14):
            date = at().date() + dt.timedelta(days=day)
            for slot in ("morning", "evening"):
                first = select_editorial_topic(date, slot,
                                              self.config["topic_groups"],
                                              self.config["editorial_limits"])
                self.assertEqual(first, select_editorial_topic(
                    date, slot, self.config["topic_groups"], self.config["editorial_limits"]))
                self.assertIn(first["theme"], self.config["topic_groups"][first["topic_group"]])
        # Extra slots should not echo the morning or earlier new-slot topic.
        for day in range(30):
            date = at().date() + dt.timedelta(days=day)
            chosen = [select_editorial_topic(date, slot, self.config["topic_groups"],
                                             self.config["editorial_limits"])["theme"]
                      for slot in ("morning", "midday", "afternoon")]
            self.assertEqual(len(chosen), len(set(chosen)))

    def test_midday_afternoon_copy_is_ordinary_and_grounded_to_daypart(self):
        for hour, slot in ((12, "midday"), (16, "afternoon")):
            prompt = json.loads(build_prompt(at(hour=hour), slot, self.config)["prompt"])
            self.assertEqual(prompt["slot"], slot)
            self.assertEqual(prompt["daypart"], "昼" if hour == 12 else "午後")
            self.assertIn("栞", json.dumps(prompt["character"], ensure_ascii=False))
            self.assertEqual(prompt["post_kind"], "everyday_chat")
            self.assertIn("固定しない", " ".join(prompt["guidelines"]))
            self.assertNotIn("寝る前", prompt["theme"])
            self.assertEqual(validate_post(ORDINARY, slot, 300), ORDINARY)

    def test_bad_article_copy_not_admitted_as_noon_or_afternoon(self):
        for hour, slot in ((12, "midday"), (16, "afternoon")):
            with self.assertRaises(ValueError):
                verify_draft({"slot": slot, "kind": "article", "text": "【PR】http://example.com"},
                             at(hour=hour), self.config)


if __name__ == "__main__":
    unittest.main()
