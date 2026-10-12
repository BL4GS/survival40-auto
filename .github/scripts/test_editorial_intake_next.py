"""Staging-only regression checks for the WordPress editorial inbox."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".github" / "scripts" / "patch_editorial_intake_next.py"
spec = importlib.util.spec_from_file_location("s40_editorial_intake", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class EditorialIntakePatchTests(unittest.TestCase):
    def test_transform_targets_exact_plugin_anchors(self):
        source = """<?php
class Survival40_Auto {
    public function __construct() {
        add_action('survival40_auto_cron', [$this, 'run_automation_cycle']);
    }
    private function auto_existing_titles($limit = 120) { return []; }
}
"""
        modified = module.transform(source)
        self.assertIn("rest_api_init", modified)
        self.assertIn("s40_editorial_plan_ingest", modified)
        self.assertIn("manage_options", modified)
        self.assertIn("must_recheck_all_wordpress_posts_including_drafts", modified)
        self.assertIn("s40_editorial_plan_queue_v1", modified)
        self.assertNotIn("wp_insert_post", modified)
        self.assertNotIn("wp_update_post", modified)
        with self.assertRaises(ValueError):
            module.transform(modified)

    def test_missing_anchor_aborts(self):
        with self.assertRaises(ValueError):
            module.transform("<?php // incomplete unknown source")

    def test_current_01921_release_workflow_does_not_use_patch(self):
        release = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        self.assertNotIn("patch_editorial_intake_next.py", release)

    def test_schema_and_disabled_pub_required(self):
        self.assertIn("survival40.wp_plan_handoff.v1", module.METHODS)
        self.assertIn("ready_to_publish", module.METHODS)
        self.assertIn("sources_checked", module.METHODS)
        self.assertIn("amazon_query", module.METHODS)
        self.assertIn("awaiting_independent_research", module.METHODS)


if __name__ == "__main__":
    unittest.main()
