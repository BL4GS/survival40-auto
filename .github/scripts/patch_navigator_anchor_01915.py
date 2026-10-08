from pathlib import Path
import re
p=Path("survival40-auto/survival40-auto.php")
s=p.read_text(encoding="utf-8")
old="if(headings[i].getBoundingClientRect().top <= Math.max(220,window.innerHeight*.40)) index=i;"
new="""var switchLine=mobile.matches
              ? Math.min(window.innerHeight*.45,350)
              : Math.min(window.innerHeight-48,Math.max(window.innerHeight*.52,panel.getBoundingClientRect().bottom-42));
            if(headings[i].getBoundingClientRect().top <= switchLine) index=i;"""
assert s.count(old)==1
s=s.replace(old,new)
s,a=re.subn(r"(?m)^(\s*\*\s*Version:\s*)0\.19\.14\s*$",r"\g<1>0.19.15",s,count=1)
s,b=re.subn(r"(?m)^(\s*const\s+VERSION\s*=\s*')0\.19\.14(';\s*)$",r"\g<1>0.19.15\2",s,count=1)
s,c=re.subn(r"<h1>Survival40 Auto v0\.19\.14</h1>","<h1>Survival40 Auto v0.19.15</h1>",s,count=1)
assert a==b==c==1
p.write_text(s,encoding="utf-8")
print("navigator theme switch line follows fixed narrator panel")
