"""Offline regression tests for read-only WordPress draft markup lint."""
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "editorial" / "draft_html_escape_check.py"
spec = importlib.util.spec_from_file_location("draft_html_escape_check", SCRIPT)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class DraftHtmlEscapeTests(unittest.TestCase):
    def test_valid_html_and_actual_newlines_are_clean(self):
        self.assertEqual(checker.lint_html('<p>Text</p>\n<h2>Heading</h2><a href="https://example.org">Link</a>'), [])

    def test_json_transport_escaping_is_not_a_markup_defect(self):
        # WordPress REST JSON encodes real newlines and attribute quotes.
        # Inspect the decoded content.raw, never the JSON wire representation.
        html = '<p>Text</p>\n<h2>Next</h2><a href="https://example.org">Link</a>'
        wire = json.dumps({"content": {"raw": html}}, ensure_ascii=False)
        self.assertIn(r'\n', wire)
        self.assertIn(r'\"', wire)
        decoded = json.loads(wire)
        self.assertEqual(checker.lint_html(checker.extract_raw_html(decoded)), [])

    def test_nested_connector_text_must_be_decoded_before_lint(self):
        html = '<p>Text</p>\n<a href="https://example.org">Link</a>'
        wrapped = {"text": json.dumps({"content": {"raw": html}})}
        decoded = json.loads(wrapped["text"])
        self.assertEqual(checker.lint_html(checker.extract_raw_html(decoded)), [])

    def test_literal_backslash_n_before_heading_is_flagged(self):
        findings = checker.lint_html(r"<p>Text</p>\n<h2>Heading</h2>")
        self.assertEqual([f["code"] for f in findings], ["literal_backslash_n_before_html_tag"])

    def test_literal_backslash_quote_in_href_is_flagged(self):
        findings = checker.lint_html(r'<a href=\"https://example.org\">Link</a>')
        self.assertEqual([f["code"] for f in findings], ["literal_backslash_quote_in_html_attribute"])

    def test_ordinary_literal_backslash_n_is_not_flagged(self):
        self.assertEqual(checker.lint_html(r"Explain \n as two characters in prose."), [])

    def test_code_examples_are_ignored(self):
        raw = r'<pre><code>\n<h2>demo</h2><a href=\"x\">x</a></code></pre>'
        self.assertEqual(checker.lint_html(raw), [])

    def test_wp_rest_shape_uses_raw_not_rendered(self):
        payload = {"content": {"raw": r"<p>Text</p>\n<h2>Next</h2>", "rendered": "<p>clean</p>"}}
        self.assertEqual(len(checker.lint_html(checker.extract_raw_html(payload))), 1)

    def test_cli_detects_without_echoing_article_content(self):
        payload = {"content": {"raw": r'<a href=\"https://private.example/path\">secret prose</a>'}}
        result = subprocess.run([sys.executable, str(SCRIPT), "-"], input=json.dumps(payload), text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertTrue(json.loads(result.stdout)["findings"])
        self.assertNotIn("private.example", result.stdout)
        self.assertNotIn("secret prose", result.stdout)

    def test_cli_refuses_missing_raw(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "-"], input='{"content":{"rendered":"text"}}', text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
