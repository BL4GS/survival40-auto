"""Regression checks for retired A8 campaigns in staged-only patch scripts."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
RETIRED = ("s00000026776002", "s00000021920005")
ACTIVE = "s00000007191012"


class RetiredAffiliateGuards(unittest.TestCase):
    def test_staged_matching_no_retired_seed_or_mapping(self):
        source = (ROOT / ".github/scripts/patch_affiliate_matching_staged.py").read_text(encoding="utf-8")
        self.assertNotIn("['id'=>'s00000026776002'", source)
        self.assertNotIn("'sleep-tracking' => ['s00000026776002']", source)
        self.assertIn("in_array($id, ['s00000026776002', 's00000021920005'], true)", source)

    def test_staged_integration_rejects_retired_even_if_saved_approved(self):
        source = (ROOT / ".github/scripts/patch_affiliate_integration_staged.py").read_text(encoding="utf-8")
        self.assertNotIn('"sleep":["s00000016652002","s00000026776002"', source)
        self.assertIn("$is_retired = in_array($id, ['s00000026776002', 's00000021920005'], true)", source)
        self.assertIn("($is_unverified || $is_retired) ? 'inactive' : 'approved'", source)
        self.assertIn("'s00000026776002', 's00000021920005'], true)) continue;", source)
        self.assertIn(ACTIVE, source)


if __name__ == "__main__":
    unittest.main()
