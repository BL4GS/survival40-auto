"""Release contract checks. Source-level only: never publish a release here."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / ".github" / "workflows" / "release.yml"
VERSION = ROOT / "version.txt"


def approval_shell():
    text = RELEASE.read_text(encoding="utf-8")
    anchor = "      - name: Publish only after explicit manual approval"
    if text.count(anchor) != 1:
        raise AssertionError("Missing single gated manual publish step")
    block = text.split(anchor, 1)[1]
    header, body = block.split("        run: |\n", 1)
    lines = []
    for line in body.splitlines():
        if line and not line.startswith("          "):
            break
        lines.append(line[10:] if line else "")
    return header, "\n".join(lines) + "\n", text


class ReleaseContractTests(unittest.TestCase):
    def test_main_version_remains_unpublished(self):
        self.assertEqual(VERSION.read_text(encoding="utf-8").strip(), "0.19.20")

    def test_manual_approval_cannot_be_bypassed_by_push(self):
        header, script, text = approval_shell()
        self.assertIn("github.event_name == 'workflow_dispatch'", header)
        self.assertIn("inputs.confirm_release == 'RELEASE-0.19.21'", header)
        self.assertIn("contents: write", text)
        self.assertIn("version.txt", text)

    def test_shell_syntax(self):
        _, script, _ = approval_shell()
        result = subprocess.run(["bash", "-n"], input=script, text=True,
                                capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_order_is_upload_verify_then_version_update(self):
        _, script, _ = approval_shell()
        self.assertIn("set -euo pipefail", script)
        upload = script.index("gh release upload latest dist/survival40-auto.zip")
        asset = script.index('ASSET_ID=')
        download = script.index("gh release download latest")
        compare = script.index("cmp dist/survival40-auto.zip")
        update = script.index('gh api -X PUT ')
        confirm = script.index('FINAL_CONTENT=')
        self.assertLess(upload, asset)
        self.assertLess(asset, download)
        self.assertLess(download, compare)
        self.assertLess(compare, update)
        self.assertLess(update, confirm)
        self.assertIn("contents/version.txt", script[update:])
        self.assertIn("test \"$REMOTE_VERSION\" = '0.19.20'", script)
        self.assertIn("-f sha=\"$REMOTE_SHA\"", script)
        self.assertIn("test \"$FINAL_CONTENT\" = '0.19.21'", script)

    def test_version_strip_handles_actual_newlines(self):
        _, script, _ = approval_shell()
        strip = "tr -d '" + chr(92) + "r" + chr(92) + "n'"
        self.assertEqual(script.count(strip), 3)
        result = subprocess.run(["bash", "-c", "printf '0.19.20\\n' | " + strip],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "0.19.20")

    def test_artifact_is_exact_zip_and_no_auto_publication(self):
        _, _, text = approval_shell()
        self.assertIn("unzip -t dist/survival40-auto.zip", text)
        self.assertIn("survival40-0.19.21-release-review", text)
        self.assertIn("get_option('s40_affiliate_frontend_enabled', 'no') !== 'yes'", text)


if __name__ == "__main__":
    unittest.main()
