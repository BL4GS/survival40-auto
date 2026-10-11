import datetime as dt
import unittest
from zoneinfo import ZoneInfo
from scripts.threads.compose import choose_slot, select_theme, validate_post

class ThreadsDraftTests(unittest.TestCase):
    def at(self, hour, minute=0):
        return dt.datetime(2026, 10, 11, hour, minute, tzinfo=ZoneInfo("Asia/Tokyo"))
    def test_slots(self):
        self.assertEqual(choose_slot(self.at(8)), "morning")
        self.assertEqual(choose_slot(self.at(20, 23)), "evening")
        self.assertIsNone(choose_slot(self.at(9)))
        self.assertIsNone(choose_slot(self.at(21)))
    def test_override_for_manual_preview(self):
        self.assertEqual(choose_slot(self.at(1), "morning"), "morning")
        with self.assertRaises(ValueError):
            choose_slot(self.at(8), "other")
    def test_topic_is_stable_for_date(self):
        topics=["a", "b", "c"]
        self.assertEqual(select_theme(self.at(8).date(),"morning",topics),
                         select_theme(self.at(8).date(),"morning",topics))
    def test_greetings(self):
        self.assertIn("おはようございます", validate_post(
            "おはようございます！今日も無理せず、自分のペースで始めてみましょう。", "morning",300))
        self.assertIn("お疲れ様です", validate_post(
            "お疲れ様です！今日もいろいろあった一日でしたね。少し自分の時間を作れますように。", "evening",300))
    def test_prevent_claims_and_promotions(self):
        for text in ("おはようございます！今日は祝日ですね。ゆっくり休んでくださいね。",
                     "おはようございます！今日も頑張りましょう。https://example.com"):
            with self.assertRaises(ValueError):
                validate_post(text,"morning",300)
    def test_bad_salutation(self):
        with self.assertRaises(ValueError):
            validate_post("今日も一日お疲れ様でした。皆さん、おやすみなさい。","morning",300)
if __name__ == "__main__":
    unittest.main()
