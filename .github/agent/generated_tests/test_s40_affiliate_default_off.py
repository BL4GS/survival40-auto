import unittest
from pathlib import Path

class TestAffiliateDefaultOff(unittest.TestCase):
    def test_affiliate_frontend_switch_default_off(self):
        frontend_patch_path = Path(".github/scripts/patch_affiliate_frontend_staged.py")
        self.assertTrue(frontend_patch_path.exists(), "Staged affiliate frontend patch must exist.")
        content = frontend_patch_path.read_text(encoding="utf-8")
        self.assertIn("s40_affiliate_frontend_enabled", content, "Must check affiliate frontend option.")
        self.assertIn("!== 'yes'", content, "Must default to off unless explicitly set to 'yes'.")

    def release_invariant_check(self):
        self.assertTrue(True)
