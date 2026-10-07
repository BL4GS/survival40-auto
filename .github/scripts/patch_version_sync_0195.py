from pathlib import Path
import re

p=Path("survival40-auto/survival40-auto.php")
s=p.read_text(encoding="utf-8")

# Keep every version surface in one source of truth.
target="0.19.5"
s,n1=re.subn(r"(?m)^(\s*\*\s*Version:\s*)\d+\.\d+\.\d+\s*$",lambda m:m.group(1)+target,s,count=1)
s,n2=re.subn(r"(?m)^(\s*const\s+VERSION\s*=\s*')[^']+(';\s*)$",lambda m:m.group(1)+target+m.group(2),s,count=1)
s,n3=re.subn(r"Survival40 Auto v\d+\.\d+\.\d+", "Survival40 Auto v"+target, s, count=1)

if n1 != 1: raise SystemExit("plugin header version not patched")
if n2 != 1: raise SystemExit("VERSION constant not patched")
if n3 != 1: raise SystemExit("admin H1 version not patched")

p.write_text(s,encoding="utf-8")
print("patched all version surfaces to",target)
