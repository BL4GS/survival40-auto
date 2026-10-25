"""Advance Shiori's mobile heading-title switch near the viewport center without touching desktop behavior.

Run against the reconstructed PHP during the reviewed release build, after
patch_navigator_anchor_01915.py and before packaging. Fail closed on drift.
"""
from pathlib import Path

p = Path("survival40-auto/survival40-auto.php")
source = p.read_text(encoding="utf-8")
old = "? Math.min(window.innerHeight*.45,350)"
new = "? Math.min(window.innerHeight*.82,600)"
assert source.count(old) == 1, "Shiori mobile switch threshold changed; review manually"
assert source.count(new) == 0, "Shiori mobile switch fix already applied"
p.write_text(source.replace(old, new, 1), encoding="utf-8")
print("Shiori mobile heading switch moved earlier toward viewport center; desktop untouched")
