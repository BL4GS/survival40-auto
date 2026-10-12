"""Regression tests for NEXT-release fail-closed planner patch, no WP site calls."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parent / "patch_planner_failclosed_next.py"
spec = importlib.util.spec_from_file_location("s40_planner_failclosed_next", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

OLD = """        if (!is_array($data)) {
            $fallback_title = '40代男性のスキンケア基本｜老け見えを防ぐ最低限の習慣';
            $base_title = $fallback_title;
            $n = 2;
            $existing_keys = array_map([$this, 'normalize_title_key'], $titles);
            while (in_array($this->normalize_title_key($fallback_title), $existing_keys, true)) {
                $fallback_title = $base_title . ' 実践編' . $n;
                $n++;
            }
            $data = [
                'title' => $fallback_title,
                'keyword' => '40代 男性 スキンケア 基本',
                'category' => '肌・老け見え',
                'excerpt' => '40代男性が毎日続けやすい最低限のスキンケアを、洗顔・保湿・紫外線対策の順に整理します。',
                'seo_title' => $fallback_title,
                'amazon_query' => 'メンズ オールインワン 保湿',
                'reason' => '企画JSON不備のため自動フォールバック: ' . $planner_error,
            ];
        }

        $title = sanitize_text_field($data['title']);"""


class FailclosedPlannerTests(unittest.TestCase):
    def test_fallback_replaced_with_nonpublishing_error(self):
        before = "PREVIOUS_BLOCK;\n" + OLD + "\nFOLLOWING_BLOCK;"
        after = module.transform(before)
        self.assertIn("new WP_Error(", after)
        self.assertIn("s40_plan_unavailable", after)
        self.assertIn("自動生成を停止しました", after)
        self.assertNotIn("実践編", after)
        self.assertNotIn("メンズ オールインワン", after)
        self.assertTrue(after.startswith("PREVIOUS_BLOCK;\n"))
        self.assertTrue(after.endswith("\nFOLLOWING_BLOCK;"))
        self.assertEqual(after.count("sanitize_text_field($data['title'])"), 1)

    def test_unknown_upstream_planner_never_patched(self):
        with self.assertRaises(ValueError):
            module.transform("<?php echo 'unreviewed code'; ?>")

    def test_patch_is_one_time_only(self):
        after = module.transform(OLD)
        with self.assertRaises(ValueError):
            module.transform(after)

    def test_requires_exact_safeguard_anchor_once(self):
        before = OLD + "\n" + OLD
        with self.assertRaises(ValueError):
            module.transform(before)

    def test_release_01921_does_not_invoke_new_patch(self):
        release = Path(".github/workflows/release.yml").read_text(encoding="utf-8")
        self.assertNotIn("patch_planner_failclosed_next.py", release)
        self.assertIn("RELEASE-0.19.21", release)


if __name__ == "__main__":
    unittest.main()
