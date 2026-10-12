import datetime as dt
import json
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from scripts.threads.compose import (
    choose_slot, gemini_generate, select_shape, select_theme, validate_post,
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


if __name__ == "__main__":
    unittest.main()
