import datetime as dt
import json
import unittest
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

from scripts.threads.compose import CONFIG
from scripts.threads.prepare_schedule import (
    ARTICLE_CALENDAR, FIRST_TEXT, choose_copy, add_morning_greeting, MORNING_GREETING,
)
from scripts.threads.scheduled_publisher import (
    assert_scheduled_env, publish, verify_draft,
)

JST = ZoneInfo("Asia/Tokyo")
ENV = {
    "GITHUB_EVENT_NAME": "schedule",
    "GITHUB_REPOSITORY": "BL4GS/survival40-auto",
    "GITHUB_REF": "refs/heads/main",
    "THREADS_ACCESS_TOKEN": "FAKE_TOKEN_FOR_UNIT_TEST_ONLY",
    "THREADS_USER_ID": "1234567",
    "GITHUB_TOKEN": "FAKE_GITHUB_TOKEN",
}


class ScheduledLiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))

    @staticmethod
    def when(year=2026, month=10, day=13, hour=20, minute=5):
        return dt.datetime(year, month, day, hour, minute, tzinfo=JST)

    @staticmethod
    def draft(text, when, kind="everyday", title=None):
        slot = "evening" if when.hour == 20 else "morning"
        return {
            "id": when.date().isoformat() + "-" + slot,
            "date_jst": when.date().isoformat(),
            "slot": slot, "account": "@survival40_jp",
            "kind": kind, "article_title": title,
            "text": text, "publish": False,
            "status": "prepared_for_separate_publish_gate",
            "generated_at_jst": when.isoformat(),
        }

    def test_first_evening_only_human_approved_copy(self):
        at = self.when()
        prepared = choose_copy(at, self.config, None)
        self.assertEqual(prepared["text"], FIRST_TEXT)
        self.assertEqual(prepared["kind"], "everyday")
        self.assertEqual(verify_draft(prepared, at, self.config), FIRST_TEXT)
        self.assertIsNone(choose_copy(self.when(day=13, hour=19), self.config, None))
        self.assertIsNone(choose_copy(self.when(day=12), self.config, None))
        with self.assertRaises(ValueError):
            verify_draft(dict(prepared, text="Survival40のThreads投稿テストです。"), at, self.config)

    def test_four_sourced_article_permalinks_replace_regular_evenings(self):
        self.assertEqual(len(ARTICLE_CALENDAR), 4)
        for date, article in ARTICLE_CALENDAR.items():
            at = dt.datetime.fromisoformat(date + "T20:05:00+09:00")
            prepared = choose_copy(at, self.config, None)
            self.assertEqual(prepared["kind"], "article")
            self.assertEqual(prepared["article_title"], article["title"])
            self.assertIn("https://www.survival40.com/" + article["slug"] + "/", prepared["text"])
            self.assertTrue(prepared["text"].startswith("【PR】"))
            self.assertEqual(verify_draft(prepared, at, self.config), prepared["text"])
            with self.assertRaises(ValueError):
                verify_draft(dict(prepared, text=prepared["text"].replace(
                    "www.survival40.com", "example.org")), at, self.config)

    def test_normal_posts_generate_only_in_valid_slots(self):
        at = self.when(day=15, hour=8)
        with patch("scripts.threads.prepare_schedule.gemini_generate") as gemini:
            gemini.return_value = "洗面台の小物が増えてしまって、片づけるより先に新しい置き場所を考えています。"
            prepared = choose_copy(at, self.config, "FAKE_GEMINI")
            self.assertEqual(prepared["kind"], "everyday")
            self.assertEqual(
                verify_draft(prepared, at, self.config),
                MORNING_GREETING + "\n" + gemini.return_value
            )
            gemini.assert_called_once()
        with self.assertRaises(ValueError):
            choose_copy(at, self.config, None)

    def test_morning_greeting_is_exact_and_not_duplicated(self):
        at = self.when(day=15, hour=8)
        with patch("scripts.threads.prepare_schedule.gemini_generate") as gemini:
            gemini.return_value = (
                "おはようございます。洗面台に増えていく小物、"
                "きれいに片づけたつもりでも翌朝には元通りです。"
            )
            prepared = choose_copy(at, self.config, "FAKE_GEMINI")
        self.assertEqual(prepared["kind"], "everyday")
        self.assertTrue(prepared["text"].startswith(MORNING_GREETING + "\n"))
        self.assertEqual(prepared["text"].count("おはようございます"), 1)
        self.assertEqual(verify_draft(prepared, at, self.config), prepared["text"])

    def test_greeting_is_only_morning_evening_is_unforced(self):
        eve = self.when(day=15, hour=20)
        with patch("scripts.threads.prepare_schedule.gemini_generate",
                   return_value="部屋着に着替えて、郵便物のことを思い出しました。") as generated:
            draft = choose_copy(eve, self.config, "FAKE_GEMINI")
        self.assertTrue(draft["text"].startswith("部屋着に"))
        self.assertNotIn(MORNING_GREETING, draft["text"])
        self.assertEqual(verify_draft(draft, eve, self.config), generated.return_value)

    def test_missing_morning_greeting_rejected_by_live_gate(self):
        at = self.when(day=15, hour=8)
        raw = "片づけても翌朝にはまた小物が増えています。"
        greeting = add_morning_greeting(raw)
        draft = self.draft(greeting, at)
        self.assertEqual(verify_draft(draft, at, self.config), greeting)
        with self.assertRaisesRegex(ValueError, "opening greeting"):
            verify_draft(dict(draft, text=raw), at, self.config)
        with self.assertRaisesRegex(ValueError, "content beyond"):
            add_morning_greeting("おはようございます。")

    def test_invalid_env_ref_event_and_missing_tokens_never_publish(self):
        for replacement in (
            {"GITHUB_EVENT_NAME": "workflow_dispatch"},
            {"GITHUB_REPOSITORY": "other/repo"},
            {"GITHUB_REF": "refs/heads/feature"},
            {"THREADS_ACCESS_TOKEN": ""},
            {"THREADS_USER_ID": "abc"},
            {"GITHUB_TOKEN": ""},
        ):
            with self.subTest(replacement=replacement):
                with self.assertRaises(ValueError):
                    assert_scheduled_env(dict(ENV, **replacement))

    def test_invalid_or_stale_drafts_are_rejected(self):
        at = self.when(day=15, hour=20)
        prepared = self.draft("洗面台の小物がいつの間にか増えていて、何から片づけるか迷っています。", at)
        for replacement in (
            {"date_jst": "2026-10-14"},
            {"id": "2026-10-14-evening"},
            {"account": "@different"},
            {"publish": True},
            {"status": "published"},
            {"generated_at_jst": "2026-10-15T19:30:00+09:00"},
            {"text": "https://not-allowed.example.org/example"},
        ):
            with self.subTest(replacement=replacement):
                with self.assertRaises(ValueError):
                    verify_draft(dict(prepared, **replacement), at, self.config)

    def test_publish_orders_preflight_ledger_and_single_meta_sequence(self):
        at = self.when()
        prepared = choose_copy(at, self.config, None)
        called = []
        with (patch("scripts.threads.token_preflight.safe_get") as safe,
              patch("scripts.threads.token_preflight.validate_profile") as profile,
              patch("scripts.threads.token_preflight.validate_debug_response") as debug,
              patch("scripts.threads.scheduled_publisher.MetaThreadsClient") as meta_class,
              patch("scripts.threads.scheduled_publisher.GithubLedger") as ledger_class):
            safe.side_effect = lambda *args, **kwargs: (
                {"id": "1234567", "username": "survival40_jp"}
                if args[0] == "/me" else {"data": {"is_valid": True}}
            )
            client = meta_class.return_value
            client.verify_account.side_effect = lambda *x: called.append("identity")
            client.create_text_container.side_effect = lambda *x: (called.append("container") or "321")
            client.publish_container.side_effect = lambda *x: (called.append("publish") or "654")
            ledger = ledger_class.return_value
            ledger.reserve.side_effect = lambda *x: (called.append("reserve") or True)
            ledger.mark_published.side_effect = lambda *x: called.append("mark")
            self.assertEqual(publish(prepared, at, self.config, ENV), "654")
            self.assertEqual(called, ["identity", "reserve", "container", "publish", "mark"])
            self.assertEqual(ledger.reserve.call_count, 1)
            self.assertEqual(client.create_text_container.call_count, 1)
            self.assertEqual(client.publish_container.call_count, 1)
            self.assertEqual(safe.call_count, 2)
            profile.assert_called_once()
            debug.assert_called_once()

    def test_already_reserved_never_posts_again(self):
        at = self.when()
        prepared = choose_copy(at, self.config, None)
        with (patch("scripts.threads.token_preflight.safe_get") as safe,
              patch("scripts.threads.token_preflight.validate_profile"),
              patch("scripts.threads.token_preflight.validate_debug_response"),
              patch("scripts.threads.scheduled_publisher.MetaThreadsClient") as meta,
              patch("scripts.threads.scheduled_publisher.GithubLedger") as ledger):
            safe.return_value = {}
            ledger.return_value.reserve.return_value = False
            self.assertIsNone(publish(prepared, at, self.config, ENV))
            meta.return_value.create_text_container.assert_not_called()
            meta.return_value.publish_container.assert_not_called()

    def test_failed_token_preflight_never_creates_ledger_or_posts(self):
        at = self.when()
        prepared = choose_copy(at, self.config, None)
        with (patch("scripts.threads.token_preflight.safe_get", side_effect=RuntimeError("offline")),
              patch("scripts.threads.scheduled_publisher.MetaThreadsClient") as meta,
              patch("scripts.threads.scheduled_publisher.GithubLedger") as ledger):
            with self.assertRaises(RuntimeError):
                publish(prepared, at, self.config, ENV)
            ledger.assert_not_called()
            meta.assert_not_called()


if __name__ == "__main__":
    unittest.main()
