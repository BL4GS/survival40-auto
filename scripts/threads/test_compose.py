import datetime as dt
import json
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from scripts.threads.article_copy import build_article_prompt
from scripts.threads.compose import (
    CONFIG, build_prompt, choose_slot, gemini_generate, select_editorial_topic,
    select_persona_angle, select_shape, select_theme, select_tone_mode, validate_post,
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

    def test_flexible_topic_selection_stays_within_allowed_scope(self):
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        policy = config["editorial_limits"]
        self.assertEqual(policy["max_small_talk_per_14_slots"], 2)
        self.assertEqual(sum(policy["soft_weights"].values()), 11)
        monday = dt.date(2026, 10, 12)
        distributions = []
        for week in range(16):
            week_start = monday + dt.timedelta(weeks=week)
            counts = {key: 0 for key in config["topic_groups"]}
            for day in range(7):
                when = week_start + dt.timedelta(days=day)
                for slot in ("morning", "evening"):
                    result = select_editorial_topic(
                        when, slot, config["topic_groups"], policy
                    )
                    group = result["topic_group"]
                    counts[group] += 1
                    self.assertIn(result["theme"], config["topic_groups"][group])
                    self.assertEqual(result, select_editorial_topic(
                        when, slot, config["topic_groups"], policy
                    ))
                    if slot == "morning":
                        self.assertNotIn("寝る前", result["theme"])
                        self.assertNotIn("帰宅後", result["theme"])
                    else:
                        self.assertNotIn("朝", result["theme"])
            self.assertEqual(sum(counts.values()), 14)
            self.assertLessEqual(counts["small_talk"], 2)
            distributions.append(tuple(counts.values()))
        # The distribution is deliberately not fixed to 8/3/2/1 weekly.
        self.assertGreater(len(set(distributions)), 1)
        self.assertEqual(config["mode"], "draft_only")

    def test_persona_scope_and_small_talk_caps_fail_closed(self):
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        groups = config["topic_groups"]
        policy = config["editorial_limits"]
        cases = [
            dict(policy, max_small_talk_per_14_slots=3),
            dict(policy, max_small_talk_per_14_slots=-1),
            dict(policy, soft_weights=dict(policy["soft_weights"], small_talk=0)),
            dict(policy, soft_weights=dict(policy["soft_weights"], celebrities=10)),
        ]
        for bad in cases:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    select_editorial_topic(
                        dt.date(2026, 10, 12), "morning", groups, bad
                    )
        with self.assertRaises(ValueError):
            select_editorial_topic(
                dt.date(2026, 10, 12), "morning",
                dict(groups, celebrities=["最新芸能ニュース"]), policy
            )

    def test_character_angle_is_optional_and_stable(self):
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        angles = config["character"]["everyday_angles"]
        seen = set()
        for days in range(25):
            now = self.at(8) + dt.timedelta(days=days)
            data = json.loads(build_prompt(now, "morning", config)["prompt"])
            self.assertIn(data["persona_angle"], angles)
            self.assertIn("人柄", data["editorial_goal"])
            self.assertIn("自然", data["character"]["autonomy"])
            self.assertIn("Survival40", data["character"]["identity"])
            seen.add(data["persona_angle"])
            self.assertEqual(data["persona_angle"], select_persona_angle(
                now.date(), "morning", angles))
        self.assertGreater(len(seen), 3)

    def test_prompt_keeps_unrelated_small_talk_closed(self):
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        for d in range(21):
            now = self.at(8) + dt.timedelta(days=d)
            for slot in ("morning", "evening"):
                data = json.loads(build_prompt(now, slot, config)["prompt"])
                self.assertIn(data["topic_group"], config["topic_groups"])
                if data["topic_group"] == "small_talk":
                    self.assertIn("政治", data["topic_guardrail"])
                    self.assertIn("少数枠", data["topic_guardrail"])
                else:
                    self.assertIn("Survival40", data["topic_guardrail"])

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

    def test_daily_chat_stays_distinct_from_article_promotion(self):
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        data = json.loads(build_prompt(self.at(8), "morning", config)["prompt"])
        self.assertEqual(data["post_kind"], "everyday_chat")
        self.assertNotIn("approved_clarity_examples", data)
        priorities = " ".join(data["editorial_priority"])
        self.assertIn("どうでもいい小さな話", priorities)
        self.assertIn("人柄", priorities)
        self.assertIn("言葉の主語は栞さん", priorities)
        self.assertIn("役立つ情報を教える記事紹介とは役割が違う", priorities)
        self.assertIn("短く素直に話せるなら一文", priorities)
        self.assertIn("話題は再登場して構わない", priorities)
        self.assertIn("25〜100字", " ".join(data["guidelines"]))
        self.assertEqual(config["editorial_modes"]["article_introduction"]["activation"].startswith("このモードは構想"), True)
        self.assertEqual(config["mode"], "draft_only")

    def test_small_fictional_everyday_anecdotes_are_allowed_in_persona(self):
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        for slot, hour in (("morning", 8), ("evening", 20)):
            payload = json.loads(build_prompt(self.at(hour), slot, config)["prompt"])
            priorities = " ".join(payload["editorial_priority"])
            guidelines = " ".join(payload["guidelines"])
            self.assertIn("一人称で創作してよい", priorities)
            self.assertIn("ちょっと情けない失敗", priorities)
            self.assertIn("小さな一人称エピソードは創作してよい", guidelines)
            self.assertIn("使用レビュー", guidelines)
            self.assertIn("効果", guidelines)
            self.assertIn("家族", priorities)
            self.assertNotIn("一人称の作り話は禁止", priorities)
            self.assertNotIn("個人の実体験を創作しない", payload["shape_notes"])
        self.assertIn("fictional_micro_anecdotes",
                      config["editorial_modes"]["everyday_chat"])
        self.assertIn("使用実績", config["voice"]["persona_policy"])
        self.assertEqual(config["mode"], "draft_only")

    def test_article_intro_uses_only_supplied_article_text(self):
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        article = {
            "title": "40代男性のスキンケアの話",
            "url": "https://survival40.com/skin-care-guide/",
            "text": "これは記事本文の抜粋です。" * 12,
        }
        data = json.loads(build_article_prompt(article, config))
        self.assertEqual(data["post_kind"], "article_introduction")
        self.assertFalse(data["publication"])
        self.assertEqual(data["article"]["excerpt"], article["text"])
        self.assertIn("抜粋から分からない効果", " ".join(data["guidelines"]))

    def test_article_introduction_refuses_unknown_or_external_sources(self):
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        valid = {
            "title": "40代男性のスキンケアの話",
            "url": "https://survival40.com/skin-care-guide/",
            "text": "これは記事本文の抜粋です。" * 12
        }
        for bad in (
            dict(valid, text="要点なし"),
            dict(valid, title=""),
            dict(valid, url="https://unrelated.com/skin-care-guide/"),
            dict(valid, url="http://survival40.com/skin-care-guide/"),
            dict(valid, url="https://survival40.com.evil.net/skin-care-guide/"),
            dict(valid, url="https://survival40.com/"),
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    build_article_prompt(bad, config)
        with self.assertRaises(ValueError):
            build_article_prompt(valid, dict(config, mode="auto_publish"))

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
