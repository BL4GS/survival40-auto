import datetime as dt
import json
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from scripts.threads.compose import (
    CONFIG, build_prompt, choose_slot, gemini_generate, select_editorial_topic,
    select_shape, select_theme, select_tone_mode, validate_post,
)


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

    def test_theme_and_shape_are_stable_per_date_and_slot(self):
        themes = ["a", "b", "c"]
        self.assertEqual(
            select_theme(self.at(8).date(), "morning", themes),
            select_theme(self.at(8).date(), "morning", themes),
        )
        shapes = {select_shape(self.at(8).date(), slot) for slot in ("morning", "evening")}
        self.assertTrue(shapes.issubset({
            "short_observation", "small_detail", "quiet_remark", "light_question"
        }))

    def test_editorial_topic_mix_is_bounded_each_iso_week(self):
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        limits = config["editorial_limits"]["per_14_weekly_slots"]
        self.assertEqual(limits, {
            "grooming": 8, "movement": 3,
            "daily_routine": 2, "small_talk": 1,
        })
        monday = dt.date(2026, 10, 12)
        for w in range(12):
            week_start = monday + dt.timedelta(weeks=w)
            counts = {key: 0 for key in limits}
            for d in range(7):
                day = week_start + dt.timedelta(days=d)
                for slot in ("morning", "evening"):
                    topic = select_editorial_topic(
                        day, slot, config["topic_groups"], limits
                    )
                    counts[topic["topic_group"]] += 1
                    self.assertIn(topic["theme"], config["topic_groups"][topic["topic_group"]])
                    if slot == "morning":
                        self.assertNotIn("寝る前", topic["theme"])
                        self.assertNotIn("帰宅後", topic["theme"])
                    else:
                        self.assertNotIn("朝", topic["theme"])
            self.assertEqual(counts, limits)
        self.assertEqual(config["mode"], "draft_only")

    def test_no_category_broadening_or_increased_chatter_quota(self):
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        groups = config["topic_groups"]
        limits = config["editorial_limits"]["per_14_weekly_slots"]
        for changes in (
            {"small_talk": 2, "grooming": 7},
            {"small_talk": 10, "grooming": -1, "movement": 3, "daily_routine": 2},
        ):
            wrong = dict(limits, **changes)
            with self.assertRaises(ValueError):
                select_editorial_topic(dt.date(2026, 10, 12), "morning", groups, wrong)
        with self.assertRaises(ValueError):
            select_editorial_topic(
                dt.date(2026, 10, 12), "morning",
                dict(groups, unrelated_celebrity=["芸能ニュース"]), limits
            )

    def test_prompt_keeps_unrelated_small_talk_closed(self):
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        for d in range(14):
            date = self.at(8) + dt.timedelta(days=d)
            for slot in ("morning", "evening"):
                prompt = json.loads(build_prompt(date, slot, config)["prompt"])
                group = prompt["topic_group"]
                self.assertIn(group, config["topic_groups"])
                if group == "small_talk":
                    self.assertIn("政治", prompt["topic_guardrail"])
                    self.assertIn("最大1回", prompt["topic_guardrail"])
                else:
                    self.assertIn("Survival40", prompt["topic_guardrail"])

    def test_natural_post_without_mandatory_greeting(self):
        self.assertEqual(validate_post(
            "洗面台に置いてあると、日焼け止めを忘れにくい。置き場所って大事。", "morning", 300
        ), "洗面台に置いてあると、日焼け止めを忘れにくい。置き場所って大事。")
        self.assertEqual(validate_post(
            "服を片づけようと思ったけど、明日の朝に回してもいい気がする。", "evening", 300
        ), "服を片づけようと思ったけど、明日の朝に回してもいい気がする。")

    def test_greetings_still_allowed_sometimes(self):
        self.assertIn("おはようございます", validate_post(
            "おはようございます。洗面台の端に、使うものだけ置くと見つけやすい。", "morning", 300
        ))

    def test_guardrails_reject_system_copy_and_sales(self):
        examples = [
            "投稿システムの連携を確認しています。現在、テストを行っています。",
            "本日は皆様に暮らしに役立つ情報をご紹介します。どうぞお楽しみに。",
            "朝の準備は小さな一歩を踏み出すことが大切です。",
            "日焼け止めを使えば必ず治るので、ぜひお試しください。",
            "今日も一日頑張りましたね。自分のペースで頑張りましょう。",
            "いつもの買い物についてはこちら https://example.com をご確認ください。",
            "今日は祝日ですね。お出かけ日和かもしれません。",
            "スキンケアの話をまとめました。 #美容 #習慣",
        ]
        for example in examples:
            with self.subTest(example=example):
                with self.assertRaises(ValueError):
                    validate_post(example, "morning", 300)

    def test_no_link_hashtag_or_question_flood(self):
        for text in ("ひとつ気になることがある。どうですか？何がいいですか？",
                     "これは気にしたいところ。#身だしなみ"):
            with self.assertRaises(ValueError):
                validate_post(text, "evening", 300)

    def test_length_and_slot_validation(self):
        with self.assertRaises(ValueError):
            validate_post("短すぎる", "morning", 300)
        with self.assertRaises(ValueError):
            validate_post("い" * 241, "morning", 300)
        with self.assertRaises(ValueError):
            validate_post("服を片づけようと思ったけど、明日の朝に回してもいい気がする。", "unknown", 300)

    def test_voice_policy_is_polite_with_rare_casual_notes(self):
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.assertIn("です・ます", config["voice"]["baseline"])
        self.assertIn("たまに", config["voice"]["occasional_relaxed_note"])
        self.assertIn("毎回は不要", config["voice"]["occasional_relaxed_note"])
        self.assertEqual(config["mode"], "draft_only")

    def test_tone_is_rare_and_no_two_consecutive_allowances(self):
        day = self.at(8).date()
        slots = []
        for offset in range(80):
            date = day + dt.timedelta(days=offset)
            for slot in ("morning", "evening"):
                slots.append(select_tone_mode(date, slot))
        casual = sum(value == "relaxed_allowed" for value in slots)
        self.assertGreater(casual, 0)
        self.assertLess(casual, len(slots) // 4)
        self.assertFalse(any(
            slots[i] == "relaxed_allowed" and slots[i + 1] == "relaxed_allowed"
            for i in range(len(slots) - 1)
        ))

    def test_prompt_guides_polite_voice_even_for_casual_allowed(self):
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        for offset in range(50):
            day = self.at(8) + dt.timedelta(days=offset)
            for slot in ("morning", "evening"):
                prompt = json.loads(build_prompt(day, slot, config)["prompt"])
                self.assertIn("です・ます", prompt["voice"]["baseline"])
                self.assertIn(prompt["tone_mode"], ("polite", "relaxed_allowed"))
                if prompt["tone_mode"] == "polite":
                    self.assertIn("意図的に挿入しない", prompt["tone_mode_instructions"])
                else:
                    self.assertIn("必要はない", prompt["tone_mode_instructions"])

    def test_clarity_examples_are_embedded_in_daily_prompt(self):
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        data = json.loads(build_prompt(self.at(8), "morning", config)["prompt"])
        self.assertEqual(len(data["approved_clarity_examples"]), 3)
        self.assertIn("一投稿一話題", " ".join(data["quality_notes"]))
        self.assertIn("論理的なつながり", " ".join(data["quality_notes"]))
        self.assertIn("比喩や抽象語", " ".join(data["quality_notes"]))
        self.assertIn("40〜100字", " ".join(data["guidelines"]))

    def test_known_unintelligible_stock_phrases_rejected(self):
        for sample in (
            "毎朝の献立を決めておくと朝の空気は少しだけ静かになります。",
            "視界に入る情報量が変わって、少し落ち着いた気持ちになります。",
            "机の上の小さな余白を見つけるのも大事かもしれませんね。",
        ):
            with self.subTest(sample=sample):
                with self.assertRaises(ValueError):
                    validate_post(sample, "morning", 300)

    def test_no_live_api_in_copy_generation(self):
        with patch("scripts.threads.compose.urllib.request.urlopen") as urlopen:
            class Response:
                def __enter__(self): return self
                def __exit__(self, *args): return False
                def read(self): return json.dumps({"candidates": [{"content": {"parts": [
                    {"text": '{"text":"洗面台に日焼け止めが置いてあると、少し忘れにくい。"}'}
                ]}}]}).encode()
            urlopen.return_value = Response()
            result = gemini_generate('{"theme":"日焼け止め"}', "FAKE_GEMINI_SECRET")
            self.assertIn("洗面台", result)
            self.assertEqual(urlopen.call_args.args[0].get_method(), "POST")
            self.assertIn("generativelanguage.googleapis.com", urlopen.call_args.args[0].full_url)
            sent = json.loads(urlopen.call_args.args[0].data.decode("utf-8"))
            system = sent["systemInstruction"]["parts"][0]["text"]
            self.assertIn("desu/masu polite style", system)
            self.assertIn("do not add casual endings", system)


if __name__ == "__main__":
    unittest.main()
