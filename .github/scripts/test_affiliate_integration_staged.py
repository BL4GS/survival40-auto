"""Offline validation for the unshipped A8 integration.
Run: python .github/scripts/test_affiliate_integration_staged.py
"""
from pathlib import Path
import json
import re
import subprocess
import tempfile

base=Path("planning/a8-banner-assets-unified-2026-10.json")
src=Path(".github/scripts/patch_affiliate_integration_staged.py")
data=json.loads(base.read_text(encoding="utf-8"))
assets=data["assets"]
assert len(assets)==16
assert len({c["program_id"] for c in assets})==16
for c in assets:
    assert c["width"]==300 and c["height"]==250
    assert c["click_url"].startswith("https://px.a8.net/svt/ejp?a8mat=")
    assert c["banner_src"].startswith("https://")
    assert c["impression_src"].startswith("https://")
    assert c["click_url"].split("a8mat=",1)[1]==c["impression_src"].split("a8mat=",1)[1]
    assert re.search(r"[?&]mid="+re.escape(c["program_id"]), c["banner_src"])
assert {"s00000021719001","s00000007191012","s00000022947002"} <= {c["program_id"] for c in assets}
script=src.read_text(encoding="utf-8")
assert 's40_affiliate_match_preview' in script
assert "if ($id === 's00000022947002') continue;" in script
assert "if (($row['status'] ?? '') !== 'approved') continue;" in script
assert "In-memory alias migration" in script
assert "no automatic posting" in script
# Compile test verifies Python syntax; this script does not patch or deploy PHP.
compile(script,str(src),"exec")
print("PASS: 16 campaigns, URL/impression pairs, ID consistency, topic guardrails and patch syntax")
