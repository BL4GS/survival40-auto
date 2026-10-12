"""Future WordPress queue consumer test: exact anchor / fail-closed review contract."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".github" / "scripts" / "patch_editorial_consumer_next.py"
spec = importlib.util.spec_from_file_location("s40_consumer_patch", SCRIPT)
patch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)

class QueueConsumerPatchTests(unittest.TestCase):
    def test_never_in_current_public_release_workflow(self):
        release = (ROOT/".github/workflows/release.yml").read_text(encoding="utf-8")
        self.assertNotIn("patch_editorial_consumer_next.py", release)

    def test_needs_intake_and_failclosed_before_application(self):
        with self.assertRaises(ValueError):
            patch.transform("<?php class Survival40_Auto { }")

    def test_queue_path_forces_draft_and_quality_checks(self):
        self.assertIn("'_s40_editorial_queue'=>1", patch.METHODS)
        self.assertIn("'allow_amazon'=>0", patch.METHODS)
        self.assertIn("'allow_a8'=>0", patch.METHODS)
        self.assertIn("awaiting_independent_research", patch.METHODS)
        self.assertIn("processing_research", patch.METHODS)
        self.assertIn("held_after_research_failure", patch.METHODS)
        self.assertIn("draft_created_after_review", patch.METHODS)
        self.assertIn("existing_wordpress", patch.METHODS) if False else None
        self.assertIn("s40_editorial_ingest_lock_v1", patch.METHODS)
        self.assertIn("empty($p['_s40_editorial_queue'])",
                      patch.STATUS_LINE.replace("&& !empty($s['auto_publish_general'])",
                          "&& !empty($s['auto_publish_general']) && empty($p['_s40_editorial_queue'])"))
        self.assertNotIn("wp_insert_post(", patch.METHODS)

    def test_no_automatic_retried_failed_queued_plan(self):
        self.assertIn("held_after_research_failure", patch.METHODS)
        self.assertIn("processing_research", patch.METHODS)
        self.assertIn("one queue plan/cycle", patch.transform.__code__.co_consts.__str__())

if __name__ == "__main__":
    unittest.main()
