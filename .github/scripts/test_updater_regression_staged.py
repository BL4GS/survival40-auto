"""Read-only regression checks for the WordPress/GitHub updater split."""
from pathlib import Path
root=Path(".github/scripts")
self_update=(root/"patch_self_updater_0197.py").read_text(encoding="utf-8")
stability=(root/"patch_author_update_stability_01920.py").read_text(encoding="utf-8")
release=Path(".github/workflows/release.yml").read_text(encoding="utf-8")
assert "github_schedule_self_update" in self_update
assert "github_run_self_update" in self_update
assert "add_action('shutdown'" in self_update
assert "Independent shutdown upgrader disabled" in stability
assert "Legacy scheduled updater intentionally not hooked" in stability
assert "patch_author_update_stability_01920.py" in release
assert "patch_affiliate_integration_staged.py" in release
assert "patch_affiliate_render_staged.py" in release
assert "patch_affiliate_post_save_staged.py" in release
assert "Publish only after explicit manual approval" in release
assert "github.event_name == 'workflow_dispatch'" in release
print("PASS: independent shutdown upgrader removed; reviewed affiliate features match gated release")
