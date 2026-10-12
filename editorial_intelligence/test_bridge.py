import copy
import unittest

from editorial_intelligence.bridge import (
    CATEGORY, HandoffError, build_handoff, classify, inspect_idea
)

def idea(title, broad="daily", ads="none", health=False):
    return {
        "title": title, "category": broad,
        "article_type": "howto",
        "reader_problem": "毎日の生活で感じる不便を少し減らし、時間の負担を軽くしたい",
        "reader_takeaway": "生活の中で無理なく取り入れられる見直しポイントと注意点がわかる",
        "research_questions": [
            "この工夫を裏付ける専門家や公的機関の資料は具体的に存在するか",
            "一般的に推奨できない使い方や安全上の注意事項はどのようなものか",
        ],
        "reason_not_duplicate": "既存記事とは異なる疑問を扱う",
        "advertising_policy": ads,
        "requires_health_evidence_review": health,
        "status": "concept_only_not_researched",
    }

def report(ideas):
    return {
        "date_jst": "2026-10-12", "ideas": ideas,
        "automatically_published": False,
        "source_validation": "not_done_yet",
    }

class WordPressPlanHandoffTests(unittest.TestCase):
    def test_mapping_exactly_matches_eight_php_category_names(self):
        self.assertEqual(set(CATEGORY), {
            "肌・老け見え", "髪・頭皮", "ニオイ・清潔感", "口・歯",
            "疲労・睡眠", "体型・筋力", "食事・栄養", "40代の不調"})

    def test_realistic_four_topic_categories(self):
        cases = [
            ("40代男性の乾燥肌対策｜化粧水がしみるようになったときの見直し方",
             "skin", "肌・老け見え"),
            ("40代男性のデスクワーク腰痛｜椅子と座り方で負担を減らす基本",
             "body", "40代の不調"),
            ("40代の白髪染めシャンプーの仕組み｜メリットと使い続ける注意点",
             "daily", "髪・頭皮"),
            ("40代からの水分補給の目安｜コーヒーとお酒が多い日のリカバリー",
             "body", "食事・栄養"),
        ]
        for title, bucket, expected in cases:
            with self.subTest(title=title):
                entry, err = inspect_idea(idea(title, bucket), [], set())
                self.assertIsNone(err)
                self.assertEqual(entry["plugin_planner_input"]["category"], expected)
                self.assertFalse(entry["safety"]["publish_authorized"])
                self.assertEqual(entry["plugin_planner_input"]["amazon_query"], "")

    def test_ambiguity_is_held(self):
        cat, reason = classify("40代のスキンケアと睡眠を一度に見直す暮らしの基本")
        self.assertIsNone(cat)
        self.assertEqual(reason, "multi_subject_review_required")

    def test_unknown_is_held(self):
        item, reason = inspect_idea(idea("毎日の暮らしを少し心地よくする方法を考えよう"), [], set())
        self.assertIsNone(item)
        self.assertEqual(reason, "unrecognized_subject")

    def test_strictly_no_ad_assignment_even_if_optional(self):
        it = idea("40代の白髪染めシャンプーの仕組みと気をつけたい基本", ads="optional")
        entry, err = inspect_idea(it, [], set())
        self.assertIsNone(err)
        self.assertEqual(entry["plugin_planner_input"]["amazon_query"], "")
        self.assertTrue(entry["safety"]["no_affiliate_assigned"])
        self.assertEqual(entry["editorial"]["advertising_policy"], "optional")

    def test_skin_health_review_not_lost(self):
        it = idea("40代男性の化粧水と乾燥肌の基本を改めて確認する", "skin", health=True)
        entry, err = inspect_idea(it, [], set())
        self.assertIsNone(err)
        self.assertTrue(entry["editorial"]["requires_ymyl_gate"])

    def test_new_live_published_title_blocks_stale_proposals(self):
        title = "40代男性の水分補給を考える朝のコーヒーの飲み方"
        handoff = build_handoff(report([idea(title, "body")]),
                                ["40代からの水分補給を考える朝のコーヒーの飲み方"])
        self.assertEqual(handoff["plans"], [])
        self.assertEqual(handoff["held"][0]["reason"], "similar_to_current_published_article")

    def test_duplicate_queue_held(self):
        it = idea("40代男性の水分補給を考える朝のコーヒーの飲み方", "body")
        handoff = build_handoff(report([it, copy.deepcopy(it)]), [])
        self.assertEqual(len(handoff["plans"]), 1)
        self.assertEqual(handoff["held"][0]["reason"], "duplicate_idea_in_queue")

    def test_medical_treatment_topic_held(self):
        it = idea("40代男性の腰痛を治す方法と処方薬の飲み方を学ぶ", "body")
        handoff = build_handoff(report([it]), [])
        self.assertEqual(handoff["plans"], [])
        self.assertEqual(handoff["held"][0]["reason"], "medical_treatment_topic_not_auto_eligible")

    def test_unresearched_input_cannot_be_marked_published(self):
        r = report([idea("40代の白髪染めシャンプーの仕組みと注意点")])
        r["automatically_published"] = True
        with self.assertRaises(HandoffError):
            build_handoff(r, [])
        r["automatically_published"] = False
        r["source_validation"] = "done"
        with self.assertRaises(HandoffError):
            build_handoff(r, [])

    def test_scope_is_nonpublishing_and_lacks_wordpress_credentials(self):
        handoff = build_handoff(report([idea("40代の白髪染めシャンプーの仕組みと注意点")]), [])
        self.assertEqual(handoff["wp_posts_written"], 0)
        self.assertFalse(handoff["ready_to_publish"])
        self.assertTrue(handoff["plans"][0]["safety"]["must_recheck_all_wordpress_posts_including_drafts"])

    def test_bucket_conflict_held(self):
        item, reason = inspect_idea(
            idea("40代男性の白髪染めシャンプーの選び方と使い方を考える", "skin"), [], set())
        self.assertIsNone(item)
        self.assertEqual(reason, "category_conflict")

if __name__ == "__main__":
    unittest.main()
