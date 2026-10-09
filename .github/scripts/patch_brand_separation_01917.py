from pathlib import Path
import re
p = Path("survival40-auto/survival40-auto.php")
s = p.read_text(encoding="utf-8")
old = "Math.max(window.innerHeight*.52,panel.getBoundingClientRect().bottom-42)"
new = "Math.max(window.innerHeight*.40,panel.getBoundingClientRect().bottom-115)"
assert s.count(old) == 1, "navigator threshold not found"
s = s.replace(old, new, 1)
hook = "        add_action('wp_footer', [$this, 'survival40_presenter_render'], 50);"
assert s.count(hook) == 1
s = s.replace(hook, hook + "\n        add_action('wp_footer', [$this, 'survival40_brand_separation'], 90);", 1)
anchor = "    public function survival40_presenter_render() {"
assert s.count(anchor) == 1
method = r'''    public function survival40_brand_separation() {
        if (is_admin() || !is_singular('post')) return;
        ?>
        <style id="s40-brand-separation">
        body.single-post .wp-block-post-author,
        body.single-post .wp-block-post-author-name,
        body.single-post .wp-block-post-author-biography,
        body.single-post .entry-meta .byline,
        body.single-post .posted-by,
        body.single-post .author-name { display:none !important; }
        </style>
        <script id="s40-brand-separation-js">
        (function(){
          var scope=document.querySelector('article .entry-content, article .wp-block-post-content, .single-post .entry-content, .single-post .wp-block-post-content');
          if(!scope)return;
          var links=scope.querySelectorAll('a');
          links.forEach(function(link){
            if((link.textContent||'').trim().replace(/\s+/g,'')!=='BL4GS作品集')return;
            var node=link;
            for(var i=0;i<4&&node&&node!==scope;i++,node=node.parentElement){
              var t=(node.textContent||'').trim().replace(/\s+/g,'');
              if(t.indexOf('小説も書いてます')>=0 && t.indexOf('BL4GS作品集')>=0 && t.length<110){
                node.remove();
                return;
              }
            }
          });
        })();
        </script>
        <?php
    }

'''
s = s.replace(anchor, method + anchor, 1)
s,a = re.subn(r"(?m)^(\s*\*\s*Version:\s*)0\.19\.16\s*$",r"\g<1>0.19.17",s,count=1)
s,b = re.subn(r"(?m)^(\s*const\s+VERSION\s*=\s*')0\.19\.16(';\s*)$",r"\g<1>0.19.17\2",s,count=1)
s,c = re.subn(r"<h1>Survival40 Auto v0\.19\.16</h1>","<h1>Survival40 Auto v0.19.17</h1>",s,count=1)
assert (a,b,c)==(1,1,1)
p.write_text(s,encoding="utf-8")
print("brand separation and navigator timing patched")
