"""Offline-only tests for review-only internal-link candidate generation."""
import unittest

from site_audit.link_opportunities import review_candidates, title_grams


def article(pid, title, category=33, body="", status="publish", link=None):
    return {
        "id": pid,
        "status": status,
        "title": {"rendered": title},
        "link": link or f"https://www.survival40.com/topic-{pid}/",
        "categories": [category],
        "content": {"rendered": "<p>本文の説明です。</p>" + body},
    }


class InternalLinkCandidateTests(unittest.TestCase):
    def test_protein_pair_same_category_and_not_linked(self):
        posts = [
            article(10, "プロテインの種類と飲み方を考える"),
            article(20, "ホエイプロテインとソイプロテインの違い"),
            article(30, "頭皮の乾燥に気づいた時の見直し方", category=29),
        ]
        result = review_candidates(posts)
        self.assertEqual(result["inspected"], 3)
        matches = [(x["source_post_id"], x["target_post_id"]) for x in result["candidates"]]
        self.assertIn((10, 20), matches)
        self.assertFalse(any(30 in pair for pair in matches))
        self.assertTrue(all(x["status"] == "REVIEW_ONLY_NOT_APPLIED" for x in result["candidates"]))

    def test_excludes_existing_article_body_link_with_tracking_query(self):
        posts = [
            article(10, "プロテインの種類と飲み方を考える",
                    body='<a href="https://survival40.com/topic-20/?utm_source=body">関連</a>'),
            article(20, "ホエイプロテインとソイプロテインの違い"),
        ]
        pairs = {(x["source_post_id"], x["target_post_id"]) for x in review_candidates(posts)["candidates"]}
        self.assertNotIn((10, 20), pairs)

    def test_never_treats_generic_40s_male_phrase_as_topic_match(self):
        posts = [
            article(10, "40代男性に必要な食生活の注意点"),
            article(20, "40代男性に必要な睡眠の注意点"),
        ]
        self.assertEqual(review_candidates(posts)["candidates"], [])

    def test_rejects_drafts_uncategorized_and_external_urls(self):
        posts = [
            article(10, "プロテインの種類と飲み方を考える"),
            article(20, "ホエイプロテインとソイプロテインの違い", status="draft"),
            article(30, "ホエイプロテインとソイプロテインの違い", category=1),
            article(40, "ホエイプロテインとソイプロテインの違い",
                    link="https://evil.test/topic-40/"),
        ]
        self.assertEqual(review_candidates(posts)["candidates"], [])
        self.assertEqual(review_candidates(posts)["inspected"], 1)

    def test_ranked_and_bounded_prioritizing_unlinked_target(self):
        posts = [
            article(10, "ホエイプロテインの種類と飲み方"),
            article(20, "プロテインの種類と飲み方について"),
            article(30, "ホエイプロテインの飲み方の疑問"),
        ]
        output = review_candidates(posts, inbound_counts={"20": 0, "30": 3}, limit=2)
        self.assertLessEqual(len(output["candidates"]), 2)
        self.assertTrue(all(c["target_known_body_inbound"] is not None for c in output["candidates"]))
        self.assertIn("No links were added", output["limitations"])

    def test_does_not_infer_links_when_metadata_absent(self):
        posts = [article(10, "プロテインの種類と飲み方を考える"),
                 article(20, "ホエイプロテインとソイプロテインの違い")]
        del posts[0]["categories"]
        self.assertEqual(review_candidates(posts)["inspected"], 1)
        self.assertEqual(review_candidates(posts)["candidates"], [])

    def test_duplicate_post_id_rejects_entire_candidate_list(self):
        posts = [article(10, "プロテインの種類と飲み方を考える"),
                 article(10, "ホエイプロテインとソイプロテインの違い")]
        report = review_candidates(posts)
        self.assertEqual(report["scope"], "duplicate_post_ids")
        self.assertEqual(report["candidates"], [])

    def test_title_html_is_unescaped_and_scripts_excluded(self):
        self.assertTrue(title_grams("プロテイン").issubset(title_grams("40代男性のプロテイン")))
        post_a = article(10, "プロテインと飲み方<script>bad</script>")
        post_b = article(20, "プロテインの飲み方")
        result = review_candidates([post_a, post_b])
        self.assertNotIn("bad", str(result))
        self.assertNotIn("<script>", str(result))

    def test_limit_and_bounded_inventory_validation(self):
        posts = [article(i, "プロテインの種類と飲み方") for i in range(1, 103)]
        report = review_candidates(posts)
        self.assertEqual(report["scope"], "inventory_too_large")
        self.assertEqual(report["candidates"], [])
        for limit in (-1, 0, 13, True, 1.5):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                review_candidates([], limit=limit)


if __name__ == "__main__":
    unittest.main()
