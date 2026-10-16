"""Source-level staging guard test: NOT a live WordPress config check."""
import unittest
from pathlib import Path


class TestAffiliateDefaultOff(unittest.TestCase):
    def test_staged_banner_needs_explicit_frontend_opt_in(self):
        script = Path(".github/scripts/patch_affiliate_frontend_staged.py")
        self.assertTrue(script.is_file(), "Reviewed staging patch must exist")
        source = script.read_text(encoding="utf-8")
        guard = "if (get_option('s40_affiliate_frontend_enabled', 'no') !== 'yes') return $content;"
        self.assertIn(guard, source, "Missing literal fail-closed default-off guard")
        self.assertIn("public function s40_affiliate_append_reviewed_banner", source)
        self.assertLess(source.index(guard), source.index("$this->s40_ad_markup_for_post"),
                        "The default-off switch must run BEFORE computing a banner")
        self.assertIn("if ($banner === '') return $content;", source)
        self.assertIn("if (is_admin() || is_feed()", source)
        self.assertIn("get_post_status($post_id) !== 'publish'", source)

    def test_staging_patch_never_changes_option_to_enabled(self):
        source = Path(".github/scripts/patch_affiliate_frontend_staged.py").read_text(encoding="utf-8")
        self.assertNotIn("update_option('s40_affiliate_frontend_enabled'", source)
        self.assertNotIn("add_option('s40_affiliate_frontend_enabled'", source)
        self.assertNotIn("delete_option('s40_affiliate_frontend_enabled'", source)


if __name__ == "__main__":
    unittest.main()
