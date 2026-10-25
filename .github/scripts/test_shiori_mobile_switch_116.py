"""Offline regression tests for the staged Shiori mobile heading switch.

The test invokes the real patch script only against disposable PHP fixtures.
No WordPress, network, release or SNS side effects are possible.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("patch_shiori_mobile_switch_116.py")
OLD = (
    "var switchLine=mobile.matches\n"
    "              ? Math.min(window.innerHeight*.45,350)\n"
    "              : Math.min(window.innerHeight-48,Math.max(window.innerHeight*.52,panel.getBoundingClientRect().bottom-42));"
)
NEW = OLD.replace(
    "? Math.min(window.innerHeight*.45,350)",
    "? Math.min(window.innerHeight*.82,600)",
)


def run_fixture(php):
    with tempfile.TemporaryDirectory() as tmp:
        plugin = Path(tmp, "survival40-auto")
        plugin.mkdir()
        file = plugin / "survival40-auto.php"
        file.write_text(php, encoding="utf-8")
        run = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=tmp, capture_output=True, text=True, timeout=5, check=False,
        )
        return run, file.read_text(encoding="utf-8")


class ShioriMobileSwitchTests(unittest.TestCase):
    def test_mobile_advanced_desktop_unchanged(self):
        unrelated = "const unrelated = '? Math.min(window.innerHeight*.45,350)';"
        original = "before\n" + OLD + "\n" + unrelated + "\nafter"
        run, result = run_fixture(original)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(result, original.replace(OLD, NEW, 1))
        self.assertIn("Math.min(window.innerHeight-48,Math.max(window.innerHeight*.52", result)
        self.assertIn(unrelated, result)

    def test_missing_or_drifted_expression_fails_without_writing(self):
        for original in (
            "unrelated php",
            OLD.replace("mobile.matches", "mobile.alternate"),
            OLD.replace("window.innerHeight*.52", "window.innerHeight*.55"),
            OLD.replace("              ?", "            ?"),
        ):
            with self.subTest(original=original[:30]):
                run, result = run_fixture(original)
                self.assertNotEqual(run.returncode, 0)
                self.assertEqual(result, original)

    def test_already_applied_fails_without_writing(self):
        run, result = run_fixture(NEW)
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(result, NEW)

    def test_duplicate_target_fails_without_writing(self):
        original = OLD + "\n" + OLD
        run, result = run_fixture(original)
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(result, original)


if __name__ == "__main__":
    unittest.main()
