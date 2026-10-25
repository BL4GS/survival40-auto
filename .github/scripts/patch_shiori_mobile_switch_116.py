"""Advance Shiori's mobile heading-title switch without changing desktop behavior.

Run against reconstructed PHP after patch_navigator_anchor_01915.py.
Match the entire switchLine expression to fail closed if either branch drifts.
This script never updates WordPress or publishes a release.
"""
from pathlib import Path

p = Path("survival40-auto/survival40-auto.php")
source = p.read_text(encoding="utf-8")
old = (
    "var switchLine=mobile.matches\n"
    "              ? Math.min(window.innerHeight*.45,350)\n"
    "              : Math.min(window.innerHeight-48,Math.max(window.innerHeight*.52,panel.getBoundingClientRect().bottom-42));"
)
new = old.replace(
    "? Math.min(window.innerHeight*.45,350)",
    "? Math.min(window.innerHeight*.82,600)",
    1,
)
assert source.count(old) == 1, "Shiori switchLine changed or duplicated; review manually"
assert source.count(new) == 0, "Shiori mobile switch fix already applied"
p.write_text(source.replace(old, new, 1), encoding="utf-8")
print("Shiori mobile switch moved earlier; desktop expression preserved")
