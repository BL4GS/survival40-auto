from pathlib import Path
import re
p=Path("survival40-auto/survival40-auto.php")
s=p.read_text(encoding="utf-8")
old="body.single-post .author-name { display:none !important; }"
new="""body.single-post .author-name,
        body.single-post .wp-block-post-author__name,
        body.single-post .wp-block-post-author__byline { display:none !important; }"""
assert s.count(old)==1
s=s.replace(old,new,1)
needle="          var links=scope.querySelectorAll('a');"
assert s.count(needle)==1
inject=r'''          // Remove a compact byline even when the theme renders it as plain text.
          var article=scope.closest('article')||document;
          article.querySelectorAll('p,span,div,small').forEach(function(el){
            if(el.children.length>2)return;
            var label=(el.textContent||'').replace(/\s+/g,'').trim();
            if(/^執筆者[:：]遊$/.test(label) || /^投稿者[:：]遊$/.test(label)){
              el.style.display='none';
            }
          });
'''
s=s.replace(needle,inject+needle,1)
s,a=re.subn(r"(?m)^(\s*\*\s*Version:\s*)0\.19\.18\s*$",r"\g<1>0.19.19",s,count=1)
s,b=re.subn(r"(?m)^(\s*const\s+VERSION\s*=\s*')0\.19\.18(';\s*)$",r"\g<1>0.19.19\2",s,count=1)
s,c=re.subn(r"<h1>Survival40 Auto v0\.19\.18</h1>","<h1>Survival40 Auto v0.19.19</h1>",s,count=1)
assert a==b==c==1
p.write_text(s,encoding="utf-8")
print("Hide article author label; keep navigator untouched")
