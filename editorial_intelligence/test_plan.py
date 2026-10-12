import datetime as dt
import json
import unittest
from unittest.mock import patch

from editorial_intelligence.plan import (
    EditorialError, collect_existing, format_markdown, gemini_topics,
    is_similar, normalize_title, prompt_for, validate_ideas
)


def existing_post(title, post_id=1, status="publish"):
    return {
        "id": post_id,
        "status": status,
        "title": {"rendered": title},
        "excerpt": {"rendered": "<p>生活のための役立つ解説。</p>"},
    }


def topic(title, category="daily", kind="howto", policy="none"):
    return {
        "title": title,
        "category": category,
        "article_type": kind,
        "reader_problem": "毎日の生活で時間を確保するのが難しくて、負担なく続く対処法を知りたい",
        "reader_takeaway": "毎日の支度を少しだけ短縮できる具体的な方法と見直すポイント",
        "research_questions": [
            "このテーマで公的機関や専門家が紹介している基本的な注意点は何か",
            "利用者が日常生活で無理なく取り入れられる工夫を裏付ける資料はあるか",
        ],
        "advertising_policy": policy,
        "reason_not_duplicate": "既存の美容商品比較ではなく日常の段取りを改善するための実践策",
    }


class TopicIntelligenceTests(unittest.TestCase):
    def test_existing_published_only(self):
        items = [
            existing_post("40代男性の肌荒れ対策を考える", 1),
            existing_post("未公開タイトル", 2, "draft"),
        ]
        catalog = collect_existing(items)
        self.assertEqual(len(catalog), 1)
        self.assertNotIn("未公開", str(catalog))

    def test_empty_catalog_blocks_generation(self):
        with self.assertRaises(EditorialError):
            collect_existing([])

    def test_duplicate_title_normalization(self):
        titles = ["40代男性の朝のスキンケア基本", "仕事帰りの足のむくみ対策"]
        self.assertTrue(is_similar("40代からの朝スキンケア基本", titles))
        self.assertFalse(is_similar("週末に手間を減らせる簡単な洗濯動線の作り方", titles))
        self.assertEqual(normalize_title("４０代男性の朝のスキンケア"), "朝のスキンケア")

    def test_guard_rejects_duplicate_and_accepts_no_ad(self):
        catalog = [{"title": "40代男性の朝のスキンケア基本"}]
        first = topic("40代からの朝スキンケア基本と続け方")
        second = topic("週末に手間を減らすための洗濯動線と片付けの工夫")
        ideas, rejected = validate_ideas([first, second], catalog)
        self.assertEqual(len(ideas), 1)
        self.assertEqual(ideas[0]["advertising_policy"], "none")
        self.assertFalse(ideas[0]["requires_health_evidence_review"])
        self.assertEqual(rejected[0]["why"], "duplicate_or_generic_title")

    def test_duplicate_within_batch(self):
        cat = [{"title": "別ジャンルの公開済み記事タイトル"}]
        candidate = topic("毎日の家事を楽にするためのちょっとした見直し方")
        ideas, rejected = validate_ideas([candidate, candidate], cat)
        self.assertEqual(len(ideas), 1)
        self.assertEqual(len(rejected), 1)

    def test_health_topic_flagged_for_research(self):
        candidate = topic("日常で続けられる乾燥対策と肌の保湿を考える", category="skin")
        ideas, _ = validate_ideas([candidate], [])
        self.assertEqual(len(ideas), 1)
        self.assertTrue(ideas[0]["requires_health_evidence_review"])

    def test_invalid_evidence_questions_and_selling_pressure_rejected(self):
        first = topic("商品をとにかく買えば解決するという宣伝企画です")
        first["research_questions"] = []
        second = topic("毎日の食生活を見直すための朝食の選び方")
        second["advertising_policy"] = "mandatory"
        ideas, rejected = validate_ideas([first, second], [])
        self.assertEqual(ideas, [])
        self.assertEqual(len(rejected), 2)

    def test_prompt_has_no_claimed_verified_sources(self):
        catalog = [{"title": "冬の保湿を考える", "excerpt": "乾燥対策の基本"}]
        prompt = json.loads(prompt_for(catalog, dt.date(2026, 10, 12)))
        self.assertEqual(prompt["date_jst"], "2026-10-12")
        self.assertTrue(any("捏造しない" in text for text in prompt["task"]))
        self.assertEqual(len(prompt["published_articles"]), 1)

    def test_markdown_discloses_not_published(self):
        idea = topic("毎日の忙しさの中で暮らしを整える簡単な方法")
        items, _ = validate_ideas([idea], [])
        report = {
            "date_jst": "2026-10-12", "existing_articles_count": 23,
            "ideas": items, "rejected": [],
        }
        written = format_markdown(report)
        self.assertIn("not verified article drafts", written)
        self.assertIn("No new article", written)

    @patch("editorial_intelligence.plan.urllib.request.urlopen")
    def test_json_response_required(self, urlopen):
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, n=-1):
                return json.dumps({
                    "candidates": [{
                        "content": {"parts": [{"text": json.dumps({"ideas": []})}]}
                    }]
                }).encode("utf-8")
        urlopen.return_value = FakeResponse()
        self.assertEqual(gemini_topics("{}", "TEST_SECRET_NOT_REAL"), [])
        req = urlopen.call_args.args[0]
        self.assertEqual(req.get_header("X-goog-api-key"), "TEST_SECRET_NOT_REAL")

    def test_model_key_required(self):
        with self.assertRaises(EditorialError):
            gemini_topics("{}", "")


if __name__ == "__main__":
    unittest.main()
