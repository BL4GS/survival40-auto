from pathlib import Path
import re
p=Path("survival40-auto/survival40-auto.php")
s=p.read_text(encoding="utf-8")
old="if(headings[i].getBoundingClientRect().top < window.innerHeight*.43) index=i;"
new="if(headings[i].getBoundingClientRect().top <= Math.min(125,window.innerHeight*.19)) index=i;"
assert s.count(old)==1
s=s.replace(old,new)
s,a=re.subn(r"(?m)^(\s*\*\s*Version:\s*)0\.19\.11\s*$",r"\g<1>0.19.12",s,count=1)
s,b=re.subn(r"(?m)^(\s*const\s+VERSION\s*=\s*')0\.19\.11(';\s*)$",r"\g<1>0.19.12\2",s,count=1)
s,c=re.subn(r"<h1>Survival40 Auto v0\.19\.11</h1>","<h1>Survival40 Auto v0.19.12</h1>",s,count=1)
assert a==b==c==1
p.write_text(s,encoding="utf-8")
print("navigator heading threshold calibrated 0.19.12")
