import unittest
from pathlib import Path

class TestAffiliateDefaultOff(unittest.TestCase):
    def test_affiliate_frontend_switch_defaults_off(self):
        patch_path = Path(".github/scripts/patch_affiliate_frontend_staged.py")
        self.assertTrue(patch_path.is_file(), "Staged affiliate frontend patch file must exist")
        content = patch_path.read_text(encoding="utf-8")
        self.assertIn("s40_affiliate_frontend_enabled", content, "Code must reference the affiliate frontend toggle")
        self.assertIn("'no'", content, "The affiliate frontend toggle must default to 'no'")

if __name__ == "__main__":
    unittest.main()
