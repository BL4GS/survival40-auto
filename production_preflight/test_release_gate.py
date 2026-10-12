"""Static guard against accidentally publishing before a read-only post check."""
from pathlib import Path
import unittest

RELEASE = Path(__file__).resolve().parents[1] / ".github/workflows/release.yml"

class ReleaseGatingTests(unittest.TestCase):
    def test_real_public_integrity_check_precedes_public_release(self):
        text = RELEASE.read_text(encoding="utf-8")
        names = [
            "      - name: Refuse release if existing public articles changed (NO WordPress writes)",
            "      - name: Publish only after explicit manual approval",
        ]
        self.assertTrue(all(text.count(x) == 1 for x in names))
        self.assertLess(text.index(names[0]), text.index(names[1]))
        gate = text.split(names[0], 1)[1].split(names[1], 1)[0]
        for snippet in (
            "if: ${{ github.event_name == 'workflow_dispatch'",
            "WEB-DB-RESTORE-VERIFIED",
            "WP-BASELINE-VERIFIED",
            "LIVE-MONITORING-READY",
            "gh run download",
            "production_preflight.verify",
            "f['unchanged']",
            "f['before_count']==23 and f['after_count']==23",
        ):
            self.assertIn(snippet, gate)
        self.assertIn("  actions: read", text)
        self.assertIn("version.txt", text)
        self.assertIn("cancel-in-progress: false", text)

if __name__ == "__main__":
    unittest.main()
