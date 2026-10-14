"""Offline-only tests for Shiori curated evergreen referrals and safe fallback."""
import datetime as dt
import json
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from scripts.threads.compose import CONFIG
from scripts.threads.evergreen_links import (
    CAMPAIGN, article_text, select_verified, slot_spec, validate_draft,
)
from scripts.threads.prepare_schedule import choose_copy
from scripts.threads.scheduled_publisher import publish, verify_draft

JST = ZoneInfo("Asia/Tokyo")
ENV = {"GITHUB_EVENT_NAME": "schedule",
       "GITHUB_REPOSITORY": "BL4GS/survival40-auto",
       "GITHUB_REF": "refs/heads/main",
       "THREADS_ACCESS_TOKEN": "TEST_META_TOKEN", "THREADS_USER_ID": "12345",
       "GITHUB_TOKEN": "TEST_GITHUB_TOKEN"}
ORDINARY = "今日は部屋着に着替えてから、しまい忘れた郵便物を思い出しました。"


def when(month=10, day=28, hour=20):
    return dt.datetime(2026, month, day, hour, 5, tzinfo=JST)


def source(now, status="publish"):
    spec = CAMPAIGN[now.date().isoformat()]
    posted = now - dt.timedelta(days=5)
    return {"id": spec[0], "status": status,
            "link": "https://www.survival40.com/" + spec[1] + "/",
            "title": {"rendered": spec[2]},
            "date_gmt": posted.astimezone(dt.timezone.utc).isoformat(),
            "content": {"rendered": "<p>" + "この記事の公開済み本文です。" * 16 + "</p>"}}


class EvergreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))

    def prepare(self, now=None, posts=None):
        now = now or when()
        if posts is None:
            posts = [source(now)]
        with (patch("scripts.threads.prepare_schedule.gemini_generate", return_value=ORDINARY),
              patch("scripts.threads.prepare_schedule.fetch_public_posts", return_value=posts)):
            return choose_copy(now, self.config, "TEST_GEMINI")

    def test_only_two_existing_evening_slots_per_week_and_protected_dates(self):
        self.assertEqual(len(CAMPAIGN), 10)
        for day, spec in CAMPAIGN.items():
            clock = dt.datetime.fromisoformat(day + "T20:05:00+09:00")
            self.assertIsNotNone(slot_spec(clock))
            self.assertIn(clock.weekday(), (2, 5))
            self.assertEqual(slot_spec(clock), spec)
            self.assertIsNone(slot_spec(clock.replace(hour=8)))
            self.assertIsNone(slot_spec(clock.replace(hour=22)))
            self.assertIsNone(slot_spec(clock - dt.timedelta(days=1)))
        for day in (14, 17, 21, 24):
            self.assertIsNone(slot_spec(when(day=day)))
        self.assertIsNone(slot_spec(when(day=29)))

    def test_valid_published_canonical_article_is_selected(self):
        clock = when()
        selected = select_verified(clock, [source(clock)])
        self.assertEqual(selected["id"], 442)
        self.assertTrue(selected["text"].startswith("【PR】"))
        self.assertTrue(selected["text"].endswith("/40s-male-scalp-shampoo-guide/"))
        self.assertEqual(verify_draft(self.prepare(clock), clock, self.config),
                         selected["text"])

    def test_reject_draft_future_wrong_slug_title_id_and_weak_body(self):
        clock = when()
        good = source(clock)
        bad = [
            dict(good, status="future"),
            dict(good, status="draft"),
            dict(good, link="https://evil.test/p/"),
            dict(good, link="https://www.survival40.com/other/"),
            dict(good, title={"rendered": "違うタイトル"}),
            dict(good, id=999),
            dict(good, content={"rendered": "<p>短い</p>"}),
            dict(good, date_gmt=(clock + dt.timedelta(days=1)).isoformat()),
        ]
        for item in bad:
            with self.subTest(post=item):
                self.assertIsNone(select_verified(clock, [item]))
        self.assertIsNone(select_verified(clock, []))
        self.assertIsNone(select_verified(clock, [object()]))
        self.assertIsNone(select_verified(when(day=29), [good]))

    def test_ad_free_editorial_copy_has_no_fake_pr_label(self):
        clock = when(day=31)
        selected = select_verified(clock, [source(clock)])
        self.assertFalse(selected["text"].startswith("【PR】"))
        self.assertIn("休憩", selected["text"])
        self.assertIn("survival40.com", selected["text"])

    def test_unavailable_article_falls_back_to_ordinary(self):
        clock = when()
        draft = self.prepare(clock, [])
        self.assertEqual(draft["kind"], "everyday")
        self.assertIsNone(draft["article_id"])
        self.assertEqual(draft["text"], ORDINARY)
        self.assertEqual(verify_draft(draft, clock, self.config), ORDINARY)
        self.assertNotIn("fallback_everyday_text", draft)

    def test_public_api_failure_falls_back_to_ordinary(self):
        clock = when()
        with (patch("scripts.threads.prepare_schedule.gemini_generate", return_value=ORDINARY),
              patch("scripts.threads.prepare_schedule.fetch_public_posts",
                    side_effect=ValueError("unavailable"))):
            draft = choose_copy(clock, self.config, "TEST_GEMINI")
        self.assertEqual(draft["kind"], "everyday")
        self.assertEqual(draft["text"], ORDINARY)

    def test_evergreen_copy_and_fallback_are_both_strictly_validated(self):
        clock = when()
        draft = self.prepare(clock)
        self.assertEqual(draft["kind"], "article")
        self.assertEqual(draft["article_id"], 442)
        self.assertEqual(draft["fallback_everyday_text"], ORDINARY)
        for patch_fields in (
            {"article_id": 999}, {"article_url": "https://evil.test/a/"},
            {"article_title": "改ざんされた記事"}, {"text": draft["text"] + "購入して"},
            {"fallback_everyday_text": "https://evil.test/"},
            {"fallback_everyday_text": ""}, {"date_jst": "2026-10-27"},
        ):
            with self.subTest(patch_fields=patch_fields), self.assertRaises(ValueError):
                verify_draft(dict(draft, **patch_fields), clock, self.config)

    def _publish_with(self, draft, clock, posts, *, exists=False, reserve=None):
        events = []
        if reserve is None:
            reserve = [True, True]
        with (patch("scripts.threads.token_preflight.safe_get", return_value={}),
              patch("scripts.threads.token_preflight.validate_profile"),
              patch("scripts.threads.token_preflight.validate_debug_response"),
              patch("scripts.threads.scheduled_publisher.MetaThreadsClient") as meta,
              patch("scripts.threads.scheduled_publisher.GithubLedger") as ledger,
              patch("scripts.threads.scheduled_publisher.fetch_public_posts",
                    return_value=posts)):
            ledger.return_value.exists.return_value = exists
            ledger.return_value.reserve.side_effect = (
                lambda *args: (events.append("reserve:" + args[0]) or reserve.pop(0))
            )
            meta.return_value.create_text_container.side_effect = (
                lambda text: (events.append("text:" + text[:14]) or "100")
            )
            meta.return_value.publish_container.side_effect = (
                lambda _: (events.append("publish") or "12345")
            )
            self.assertEqual(publish(draft, clock, self.config, ENV), "12345")
            return events, ledger.return_value, meta.return_value

    def test_new_article_reserves_identity_and_slot_before_meta(self):
        clock = when()
        draft = self.prepare(clock)
        events, ledger, meta = self._publish_with(draft, clock, [source(clock)])
        self.assertEqual(events[:2], ["reserve:2026-10-28-evening",
                                      "reserve:article-442"])
        self.assertEqual(events[-1], "publish")
        self.assertEqual(ledger.mark_published.call_count, 2)
        ledger.exists.assert_called_once_with("article-442")
        meta.create_text_container.assert_called_once_with(draft["text"])

    def test_already_introduced_article_uses_ordinary_fallback(self):
        clock = when()
        draft = self.prepare(clock)
        events, ledger, meta = self._publish_with(draft, clock, [source(clock)], exists=True)
        self.assertEqual(events[0], "reserve:2026-10-28-evening")
        self.assertNotIn("reserve:article-442", events)
        self.assertEqual(ledger.mark_published.call_count, 1)
        meta.create_text_container.assert_called_once_with(ORDINARY)

    def test_unpublished_after_preparation_uses_ordinary_fallback(self):
        clock = when()
        draft = self.prepare(clock)
        _, ledger, meta = self._publish_with(draft, clock, [source(clock, status="draft")])
        ledger.exists.assert_not_called()
        meta.create_text_container.assert_called_once_with(ORDINARY)

    def test_lost_identity_reservation_never_posts_or_retries(self):
        clock = when()
        draft = self.prepare(clock)
        with (patch("scripts.threads.token_preflight.safe_get", return_value={}),
              patch("scripts.threads.token_preflight.validate_profile"),
              patch("scripts.threads.token_preflight.validate_debug_response"),
              patch("scripts.threads.scheduled_publisher.MetaThreadsClient") as meta,
              patch("scripts.threads.scheduled_publisher.GithubLedger") as ledger,
              patch("scripts.threads.scheduled_publisher.fetch_public_posts",
                    return_value=[source(clock)])):
            ledger.return_value.exists.return_value = False
            ledger.return_value.reserve.side_effect = [True, False]
            self.assertIsNone(publish(draft, clock, self.config, ENV))
            meta.return_value.create_text_container.assert_not_called()
            meta.return_value.publish_container.assert_not_called()

    def test_main_branch_manual_workflow_never_posts(self):
        clock = when()
        draft = self.prepare(clock)
        with patch("scripts.threads.scheduled_publisher.MetaThreadsClient") as meta:
            with self.assertRaises(ValueError):
                publish(draft, clock, self.config, dict(ENV, GITHUB_EVENT_NAME="workflow_dispatch"))
            meta.assert_not_called()


if __name__ == "__main__":
    unittest.main()
