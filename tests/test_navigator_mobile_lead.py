"""Offline guardrails for changing only Shiori's phone-screen H2 trigger."""
import importlib.util
import pathlib
import unittest

BASE = pathlib.Path(__file__).resolve().parents[1]
FILE = BASE / ".github/scripts/patch_navigator_mobile_lead_01921.py"
spec = importlib.util.spec_from_file_location("mobile_lead_patch", FILE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class MobileLeadTimingTests(unittest.TestCase):
    def sample(self):
        return """function update() {
            var switchLine=mobile.matches
              ? Math.min(window.innerHeight*.45,350)
              : Math.min(window.innerHeight-48,Math.max(window.innerHeight*.40,panel.getBoundingClientRect().bottom-115));
            if(headings[i].getBoundingClientRect().top <= switchLine) index=i;
            var key=classify(h,index);
            if(active!==key) img.src=paths[key];
            txt.textContent=message;
        }"""

    def test_changes_only_mobile_threshold(self):
        before=self.sample()
        after=module.apply(before)
        self.assertEqual(after, before.replace(module.OLD,module.NEW))
        self.assertIn("Math.min(window.innerHeight*.72,580)",after)
        self.assertIn("Math.min(window.innerHeight-48,Math.max(window.innerHeight*.40",after)
        self.assertIn("txt.textContent=message",after)
        self.assertIn("var key=classify(h,index)",after)

    def test_trigger_moves_earlier_for_regular_phone_heights(self):
        for height in (568,667,812,844,896,1024):
            old=min(height*.45,350)
            new=min(height*.72,580)
            self.assertGreater(new,old)
            self.assertLess(new,height)
        self.assertEqual(min(844*.72,580),580)

    def test_fails_on_missing_duplicate_or_changed_source(self):
        with self.assertRaises(ValueError):
            module.apply(self.sample().replace(module.OLD,"? 250"))
        with self.assertRaises(ValueError):
            module.apply(self.sample()*2)
        with self.assertRaises(ValueError):
            module.apply(module.apply(self.sample()))

    def test_nothing_to_do_with_external_engagement_or_affiliates(self):
        patch=FILE.read_text(encoding="utf-8")
        self.assertNotIn("px.a8.net",patch)
        self.assertNotIn("threads_publish",patch)
        self.assertNotIn("github release",patch.lower())
        self.assertNotIn("wp_options",patch)
        self.assertIn("OLD = ",patch)
        self.assertIn("NEW = ",patch)


if __name__=="__main__":
    unittest.main()
