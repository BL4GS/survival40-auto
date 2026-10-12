import unittest
from production_preflight.baseline import snapshot
from production_preflight.verify import verify


def post(idx, title=None, html=None):
    return {
        "id": idx, "status": "publish",
        "link": "https://survival40.com/entry-" + str(idx) + "/",
        "title": {"rendered": title or "40代の毎日の暮らしの整え方"},
        "content": {"rendered": html or "<p>暮らしを少し整えます。</p>"},
    }


class UpgradePublicComparisonTests(unittest.TestCase):
    def test_identical_article_library(self):
        old = snapshot([post(7), post(8)], 2)
        new = snapshot([post(7), post(8)], 2)
        output = verify(old, new)
        self.assertTrue(output["unchanged"])
        self.assertEqual(output["before_count"], 2)
        self.assertEqual(output["after_count"], 2)
        self.assertIn("draft_count_expected_16", output["requires_wp_admin_verification"])

    def test_detects_title_and_content_changes(self):
        old = snapshot([post(7)])
        new = snapshot([post(7, title="変更後の別記事", html="<p>変更後</p>")])
        output = verify(old, new)
        self.assertFalse(output["unchanged"])
        self.assertEqual(output["changed_titles"], [7])
        self.assertEqual(output["changed_content"], [7])

    def test_detects_missing_or_new_articles(self):
        old = snapshot([post(7), post(8)])
        new = snapshot([post(8), post(9)])
        output = verify(old, new)
        self.assertEqual(output["removed"], [7])
        self.assertEqual(output["added"], [9])
        self.assertFalse(output["unchanged"])

    def test_refuses_incorrect_snapshot_size_or_schema(self):
        old = snapshot([post(7)])
        new = snapshot([post(7)])
        for invalid in (
            dict(old, schema="other"),
            dict(old, public_post_count=99),
            dict(old, production_writes=1),
            dict(old, articles=[]),
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                verify(invalid, new)

    def test_verifier_does_not_claim_private_or_ad_checks(self):
        output = verify(snapshot([post(7)]), snapshot([post(7)]))
        self.assertIn("advertising_switches_unchanged", output["requires_wp_admin_verification"])
        self.assertIn("backup_restore_rehearsal", output["requires_wp_admin_verification"])


if __name__ == "__main__":
    unittest.main()
