"""Prevent reintroducing stale-branch deadlock in the overnight GitHub agent."""
from pathlib import Path
import unittest

WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/nightly-ai-review.yml"

class NightlyContinuityContractTests(unittest.TestCase):
    def test_advisory_always_runs_even_with_pending_pr(self):
        s = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("cron: '20 18 * * *'", s)
        start = s.index("      - name: Generate bounded nightly advisory with Gemini")
        end = s.index("      - name: Archive Gemini candidate", start)
        self.assertNotIn("if: steps.pending.outputs.proceed == 'true'", s[start:end])
        self.assertIn("if: success()", s)
        self.assertIn("gh pr list --state open", s)
        self.assertIn("pull-requests: read", s)
        self.assertNotIn("git ls-remote --heads origin refs/heads/ai/nightly-candidate", s)

    def test_bounded_new_pr_is_review_only_with_unique_run_branch(self):
        s = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('BRANCH="ai/nightly-${GITHUB_RUN_ID}"', s)
        self.assertIn('gh pr create --draft', s)
        self.assertIn("needs.validate.result == 'success'", s)
        self.assertIn("permissions:\n      contents: write\n      pull-requests: write", s)
        self.assertNotIn("gh pr merge", s)
        self.assertNotIn("gh release", s)
        self.assertNotIn("wp plugin install", s)

if __name__ == "__main__":
    unittest.main()
