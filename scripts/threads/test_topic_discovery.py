"""All fixtures synthetic. No Meta or Google tokens, network or social actions."""
import datetime as dt
import json
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from scripts.threads.compose import CONFIG, build_prompt
from scripts.threads.topic_discovery import (
    KEYWORDS, ResearchUnavailable, choose_safe_signal, read_safe_signal,
    summarize, validate_signal, write_sanitized_signal, _valid_public_result,
)
from scripts.threads.prepare_schedule import choose_copy

JST = ZoneInfo("Asia/Tokyo")
NOW = dt.datetime(2026, 10, 16, 17, 0, tzinfo=JST)


def row(n, kw, now=NOW, author=None):
    date = now.astimezone(dt.timezone.utc) - dt.timedelta(hours=2)
    return {"id": str(n), "username": author or f"user_{n}",
            "text": f"{kw}について悩んでいて、選び方や普段の習慣を少し考えています。{n}",
            "timestamp": date.isoformat(),
            "permalink": f"https://www.threads.net/@user_{n}/post/post{n}"}


def fixtures(now=NOW, winning="sun"):
    groups = {}
    for topic_id, kw, _g, _t in KEYWORDS:
        groups[topic_id] = [row(i+100, kw, now) for i in range(4)] if topic_id == winning else []
    return groups


class TopicDiscoveryOffline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))

    def test_aggregate_only_public_multiple_authors_with_date(self):
        result = summarize(NOW, fixtures())
        self.assertEqual(result["topic_id"], "sun")
        self.assertEqual(result["topic_group"], "grooming")
        self.assertEqual(result["signal_strength"], "3+")
        self.assertEqual(set(result), {"schema_version", "date_jst", "topic_id",
                         "topic_group", "theme", "evidence", "signal_strength"})
        self.assertNotIn("username", str(result))
        self.assertNotIn("user_100", str(result))
        self.assertTrue(validate_signal(result))

    def test_no_public_posts_or_token_only_own_posts_no_signal(self):
        self.assertIsNone(summarize(NOW, {x[0]: [] for x in KEYWORDS}))
        own = fixtures()
        own["sun"] = [dict(x, username="survival40_jp") for x in own["sun"]]
        self.assertIsNone(summarize(NOW, own))
        self.assertIsNone(summarize(NOW, {x[0]: [row(1, x[1])]*4 for x in KEYWORDS}))
        with self.assertRaises(ResearchUnavailable):
            summarize(NOW, {"sun": []})

    def test_recent_valid_noncommercial_posts_only(self):
        kw = "筋トレ"
        self.assertIsNotNone(_valid_public_result(row(5, kw), kw, NOW))
        for edit in (
            {"username": "survival40_jp"},
            {"username": "@survival40_jp"},
            {"permalink": "https://evil.example/a"},
            {"text": "筋トレ PR案件 やります 激安"},
            {"timestamp": (NOW-dt.timedelta(days=6)).isoformat()},
            {"timestamp": (NOW+dt.timedelta(minutes=5)).isoformat()},
            {"username": "@"},
        ):
            with self.subTest(edit=edit):
                self.assertIsNone(_valid_public_result(dict(row(5, kw), **edit), kw, NOW))

    def test_signal_tampering_and_staleness_rejected(self):
        ok = summarize(NOW, fixtures())
        for bad in (
            dict(ok, theme="BUY NOW"),
            dict(ok, topic_id="fake"),
            dict(ok, evidence="copied_from_user"),
            dict(ok, user_id="123"),
            dict(ok, signal_strength="1"),
        ):
            with self.subTest(bad=bad):
                self.assertFalse(validate_signal(bad))
        tuesday = dt.datetime(2026,10,20,20,0,tzinfo=JST)
        fresh = dict(ok, date_jst=tuesday.date().isoformat())
        self.assertIsNotNone(choose_safe_signal(tuesday, fresh, self.config, "evening"))
        self.assertIsNone(choose_safe_signal(tuesday, ok, self.config, "evening"))
        self.assertIsNone(choose_safe_signal(tuesday, fresh, self.config, "morning"))
        self.assertIsNone(choose_safe_signal(tuesday.replace(day=21), fresh, self.config, "evening"))
        self.assertIsNone(choose_safe_signal(tuesday.replace(day=22), fresh, self.config, "evening"))
        self.assertIsNone(choose_safe_signal(tuesday, fresh, {"topic_groups": {}}, "evening"))

    def test_prompt_uses_allowlisted_topic_without_copied_content(self):
        tue = dt.datetime(2026, 10, 20, 20, 10, tzinfo=JST)
        sig = summarize(NOW, fixtures(winning="sleep"))
        sig["date_jst"] = tue.date().isoformat()
        wanted = choose_safe_signal(tue, sig, self.config, "evening")
        self.assertEqual(wanted["topic_group"], "daily_routine")
        prompt = json.loads(build_prompt(tue, "evening", self.config, topic_signal=wanted)["prompt"])
        self.assertEqual(prompt["theme"], "寝る前にスマホをどこに置くか")
        self.assertNotIn("Threads投稿による", str(prompt))
        with self.assertRaises(ValueError):
            build_prompt(tue, "evening", self.config,
                         topic_signal={"theme": "BUY NOW", "topic_group": "grooming"})

    def test_fail_closed_research_token_missing(self):
        tue = dt.datetime(2026, 10, 20, 20, 5, tzinfo=JST)
        with patch("scripts.threads.topic_discovery._json_request") as req:
            self.assertIsNone(read_safe_signal(tue, "", self.config, "evening"))
            req.assert_not_called()

    def test_normal_post_adapts_topic_without_changing_night_or_morning(self):
        tue = dt.datetime(2026, 10, 20, 20, 5, tzinfo=JST)
        mock = {"theme": "朝食の定番メニューを決めておくこと",
                "topic_group": "daily_routine"}
        with (patch("scripts.threads.prepare_schedule.read_safe_signal", return_value=mock),
              patch("scripts.threads.prepare_schedule.gemini_generate",
                    return_value="朝食の組み合わせを考えていたら、冷蔵庫にいつも同じ食材があることに気づきました。") as gemini):
            d = choose_copy(tue, self.config, "FAKE_GEMINI")
        prompt = json.loads(gemini.call_args[0][0])
        self.assertEqual(prompt["theme"], mock["theme"])
        self.assertEqual(d["kind"], "everyday")
        self.assertIsNone(d["article_id"])
        self.assertNotIn("https://", d["text"])
        self.assertNotIn("PR", d["text"])

    def test_no_individual_data_ever_written(self):
        signal = summarize(NOW, fixtures())
        with patch("scripts.threads.topic_discovery._json_request",
                   side_effect=ResearchUnavailable("No permission")):
            with patch("urllib.request.urlopen", side_effect=OSError("offline")):
                with self.assertRaises(ResearchUnavailable):
                    write_sanitized_signal(signal, "FAKE_GITHUB_KEY")
        self.assertEqual(len(signal), 7)


if __name__ == "__main__":
    unittest.main()
