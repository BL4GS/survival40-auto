"""Unit tests for the generated candidate gate (trusted code only)."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('s40_validator','.github/agent/validate_candidate.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
TEST='import unittest\nfrom pathlib import Path\nclass SafetyTest(unittest.TestCase):\n    def test_safe(self):\n        self.assertTrue(Path("PROJECT_VISION.md").exists())\n'
PATH='.github/agent/generated_tests/test_s40_ad_free_regression.py'

class CandidateGateTest(unittest.TestCase):
    def test_accept_safe(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(module.validate({'change':{'path':PATH,'content':TEST}},Path(root))[0],PATH)
    def test_block_release_workflow(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):
                module.validate({'change':{'path':'.github/workflows/release.yml','content':TEST}},Path(root))
    def test_block_untrusted_import(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):
                module.validate({'change':{'path':PATH,'content':TEST+'\nimport subprocess\n'}},Path(root))
    def test_block_file_write(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):
                module.validate({'change':{'path':PATH,'content':TEST+'\nPath("x").write_text("x")\n'}},Path(root))
    def test_block_existing_file(self):
        with tempfile.TemporaryDirectory() as root:
            file=Path(root)/PATH
            file.parent.mkdir(parents=True)
            file.write_text(TEST)
            with self.assertRaises(ValueError):
                module.validate({'change':{'path':PATH,'content':TEST}},Path(root))

if __name__=='__main__':
    unittest.main()
