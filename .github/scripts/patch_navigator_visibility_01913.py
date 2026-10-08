from pathlib import Path
import re
p=Path("survival40-auto/survival40-auto.php")
s=p.read_text(encoding="utf-8")
old="var content=document.querySelector('article .entry-content, article .wp-block-post-content, .single-post .entry-content, .single-post .wp-block-post-content');"
new="var content=document.querySelector('article .entry-content, article .wp-block-post-content, .single-post .entry-content, .single-post .wp-block-post-content, main article, main .entry-content, main .wp-block-post-content, article');"
assert s.count(old)==1
s=s.replace(old,new)
old2="var enough=gap>=195 && window.innerWidth>=1050;"
new2="var enough=gap>=155 && window.innerWidth>=960;"
assert s.count(old2)==1
s=s.replace(old2,new2)
old3="panel.style.left=Math.max(8,Math.round(gap-183))+'px';"
new3="panel.style.left=Math.max(8,Math.round(gap-183))+'px';"
# existing position intentionally unchanged; allow full layout to display smaller spaces
s,a=re.subn(r"(?m)^(\s*\*\s*Version:\s*)0\.19\.12\s*$",r"\g<1>0.19.13",s,count=1)
s,b=re.subn(r"(?m)^(\s*const\s+VERSION\s*=\s*')0\.19\.12(';\s*)$",r"\g<1>0.19.13\2",s,count=1)
s,c=re.subn(r"<h1>Survival40 Auto v0\.19\.12</h1>","<h1>Survival40 Auto v0.19.13</h1>",s,count=1)
assert a==b==c==1
p.write_text(s,encoding="utf-8")
print("broadened navigation article-selector/layout matching")
