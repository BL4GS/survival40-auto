"""Offline contract tests for mobile-only Shiori expandable guide."""
import importlib.util
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
PATH=ROOT/".github/scripts/patch_navigator_mobile_interaction_01921.py"
spec=importlib.util.spec_from_file_location("mobile_interaction",PATH)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class MobileInteractionTests(unittest.TestCase):
    def test_compact_and_reopenable_caption(self):
        self.assertIn("s40-collapsed",m.CSS)
        self.assertIn("max-width:52px !important",m.CSS)
        self.assertIn("pointer-events:auto !important",m.CSS)
        self.assertIn("s40-presenter-toggle:focus-visible",m.CSS)
        self.assertIn("aria-controls",m.AFTER_HTML)
        self.assertIn("aria-expanded",m.AFTER_HTML)
        self.assertIn('expandMobile(!expanded)',m.AFTER_VARIABLES)

    def test_auto_hide_and_manual_reopen(self):
        self.assertIn("window.setTimeout",m.AFTER_VARIABLES)
        self.assertIn("},4000)",m.AFTER_VARIABLES)
        self.assertIn("pinnedOpen",m.AFTER_VARIABLES)
        self.assertIn("window.clearTimeout",m.AFTER_VARIABLES)
        self.assertIn("toggle.addEventListener('click'",m.AFTER_VARIABLES)

    def test_accessible_page_only_dismiss(self):
        self.assertIn("aria-label=",m.AFTER_HTML)
        self.assertIn("栞さんの案内をこのページで閉じる",m.AFTER_HTML)
        self.assertIn("dismissed=true",m.AFTER_VARIABLES)
        self.assertNotIn("localStorage",m.AFTER_VARIABLES)
        self.assertNotIn("sessionStorage",m.AFTER_VARIABLES)
        self.assertNotIn("fetch(",m.AFTER_VARIABLES)

    def test_no_automatic_social_affiliate_or_editorial_mutation(self):
        source=PATH.read_text(encoding="utf-8")
        self.assertNotIn("threads_publish",source)
        self.assertNotIn("px.a8.net",source)
        self.assertNotIn("wp_update_post",source)
        self.assertNotIn("wp_insert_post",source)
        self.assertNotIn("admin_init",source)
        self.assertNotIn("github release",source.lower())

    def test_single_source_change_guard(self):
        for bad in ("", "blurb", 'Math.min(window.innerHeight*.45,350)'):
            with self.subTest(text=bad), self.assertRaises(ValueError):
                m.apply(bad)

    def test_existing_mobile_css_override_has_higher_specificity(self):
        self.assertIn("html body.single-post #s40-presenter.s40-visible",m.CSS)
        self.assertIn("left:auto !important",m.CSS)
        self.assertIn("right:12px !important",m.CSS)
        self.assertIn("s40-presenter.s40-visible.s40-collapsed",m.CSS)


if __name__=="__main__":
    unittest.main()
