from pathlib import Path
import re
p=Path("survival40-auto/survival40-auto.php")
s=p.read_text(encoding="utf-8")
# Preserve WordPress managed auto updates; prevent a separate shutdown upgrader
# from competing with core, which may temporarily deactivate plugins.
target="        add_action('admin_init', [$this, 'github_schedule_self_update']);"
assert s.count(target)==1
s=s.replace(target,"        // Independent shutdown upgrader disabled: WordPress owns update execution.",1)
target2="        add_action('survival40_self_update_event', [$this, 'github_run_self_update']);"
assert s.count(target2)==1
s=s.replace(target2,"        // Legacy scheduled updater intentionally not hooked.",1)
# Target only article metadata, not category, content, or other articles.
anchor="          var links=scope.querySelectorAll('a');"
assert s.count(anchor)==1
code=r'''          // The author value may already be hidden, leaving a bare text label.
          // Strip that label from text nodes within the post header only.
          var header=article.querySelector('header.entry-header, .wp-block-post-title, .entry-header');
          if(!header) header=scope.previousElementSibling;
          if(header) {
            var walker=document.createTreeWalker(header,NodeFilter.SHOW_TEXT);
            var textNode;
            while((textNode=walker.nextNode())) {
              if(/執筆者\s*[:：]/.test(textNode.nodeValue||'')) {
                textNode.nodeValue=(textNode.nodeValue||'').replace(/執筆者\s*[:：]\s*/g,'');
              }
            }
          }
'''
s=s.replace(anchor,code+anchor,1)
s,a=re.subn(r"(?m)^(\s*\*\s*Version:\s*)0\.19\.19\s*$",r"\g<1>0.19.20",s,count=1)
s,b=re.subn(r"(?m)^(\s*const\s+VERSION\s*=\s*')0\.19\.19(';\s*)$",r"\g<1>0.19.20\2",s,count=1)
s,c=re.subn(r"<h1>Survival40 Auto v0\.19\.19</h1>","<h1>Survival40 Auto v0.19.20</h1>",s,count=1)
assert a==b==c==1
p.write_text(s,encoding="utf-8")
print("updated author label and disabled competing self-upgrade scheduling")
