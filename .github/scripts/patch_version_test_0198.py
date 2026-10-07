from pathlib import Path
import re
p=Path("survival40-auto/survival40-auto.php")
s=p.read_text(encoding="utf-8")
target="0.19.8"
s,n1=re.subn(r"(?m)^(\s*\*\s*Version:\s*)\d+\.\d+\.\d+\s*$",lambda m:m.group(1)+target,s,count=1)
s,n2=re.subn(r"(?m)^(\s*const\s+VERSION\s*=\s*')[^']+(';\s*)$",lambda m:m.group(1)+target+m.group(2),s,count=1)
s,n3=re.subn(r"<h1>Survival40 Auto v\d+\.\d+\.\d+</h1>","<h1>Survival40 Auto v"+target+"</h1>",s,count=1)
if not (n1 and n2 and n3): raise SystemExit("version surfaces not found")
p.write_text(s,encoding="utf-8")
print("patched to 0.19.8")
