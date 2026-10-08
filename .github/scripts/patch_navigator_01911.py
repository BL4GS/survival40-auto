from pathlib import Path
import re

p=Path("survival40-auto/survival40-auto.php")
s=p.read_text(encoding="utf-8")
version="0.19.11"
s,a=re.subn(r"(?m)^(\s*\*\s*Version:\s*)\d+\.\d+\.\d+\s*$",lambda m:m.group(1)+version,s,count=1)
s,b=re.subn(r"(?m)^(\s*const\s+VERSION\s*=\s*')[^']+(';\s*)$",lambda m:m.group(1)+version+m.group(2),s,count=1)
s,c=re.subn(r"<h1>Survival40 Auto v\d+\.\d+\.\d+</h1>","<h1>Survival40 Auto v"+version+"</h1>",s,count=1)
if not all((a,b,c)): raise SystemExit("version surfaces not found")

# The presenter is a purely visual layer: no change to AI prompts, article content,
# affiliate links, or plugin settings. Keep it limited to front-end single posts.
hook="        add_action('wp_head', [$this, 'front_typography_guard']);"
if hook not in s: raise SystemExit("front-end hook not found")
s=s.replace(hook,hook+"\n        add_action('wp_footer', [$this, 'survival40_presenter_render'], 50);",1)

anchor="    public function front_typography_guard() {"
if anchor not in s: raise SystemExit("method insertion anchor not found")
method=r'''    public function survival40_presenter_render() {
        if (!is_singular('post') || is_admin()) return;
        $base = plugin_dir_url(__FILE__) . 'assets/navigator/';
        $states = [
            'normal' => 'normal.webp',
            'explain' => 'explain.webp',
            'caution' => 'caution.webp',
            'summary' => 'summary.webp',
        ];
        ?>
        <style id="s40-presenter-style">
          body.single-post { background:#f8f8ff; }
          #s40-presenter {
            position:fixed; z-index:30; width:174px; bottom:14px; left:8px;
            display:none; pointer-events:none; color:#273041;
            font-family:inherit; contain:layout style;
          }
          #s40-presenter.s40-visible { display:block; }
          #s40-presenter .s40-presenter-image { width:100%; height:auto; display:block; max-height:340px; object-fit:contain; object-position:bottom; }
          #s40-presenter .s40-presenter-caption {
            margin-top:-5px; background:rgba(248,248,255,.97);
            border:1px solid rgba(45,52,75,.13); border-radius:10px;
            padding:8px 10px; font-size:12px; line-height:1.5;
            box-shadow:0 4px 15px rgba(20,30,60,.08);
            overflow-wrap:anywhere;
          }
          #s40-presenter .s40-presenter-label {
            display:block; font-size:10px; letter-spacing:.04em; color:#606b80;
            margin-bottom:3px;
          }
          @media(max-width:850px) {
            #s40-presenter { position:static; width:auto; margin:0 0 20px;
              display:none; contain:none; }
            #s40-presenter.s40-visible { display:flex; flex-direction:row; align-items:end; gap:10px; }
            #s40-presenter .s40-presenter-image { flex:0 0 72px; width:72px; height:100px;
              object-fit:cover; object-position:top; }
            #s40-presenter .s40-presenter-caption { flex:1; margin:0; }
          }
          @media(prefers-reduced-motion:no-preference) {
            #s40-presenter .s40-presenter-image { transition:opacity .15s ease; }
          }
        </style>
        <aside id="s40-presenter" aria-label="Survival40 記事ナビゲーター">
          <img class="s40-presenter-image"
               src="<?php echo esc_url($base.$states['normal']); ?>"
               width="174" height="232" alt="Survival40の女性ナビゲーター"
               loading="lazy" decoding="async" />
          <div class="s40-presenter-caption" aria-live="off">
            <span class="s40-presenter-label">SURVIVAL40 GUIDE</span>
            <span class="s40-presenter-text">この記事のポイントをご案内します。</span>
          </div>
        </aside>
        <script id="s40-presenter-js">
        (function() {
          'use strict';
          var panel=document.getElementById('s40-presenter');
          if(!panel) return;
          var content=document.querySelector('article .entry-content, article .wp-block-post-content, .single-post .entry-content, .single-post .wp-block-post-content');
          if(!content) return;
          var img=panel.querySelector('img');
          var txt=panel.querySelector('.s40-presenter-text');
          var paths=<?php echo wp_json_encode(array_map(function($x)use($base){ return $base.$x; }, $states)); ?>;
          var mobile=window.matchMedia('(max-width:850px)');
          var headings=Array.prototype.slice.call(content.querySelectorAll('h2'));
          var active='';
          var ticking=false;
          Object.keys(paths).forEach(function(k) { var i=new Image(); i.src=paths[k]; });
          function classify(node,index) {
            if(!node) return 'normal';
            var label=(node.textContent||'').trim();
            if(/まとめ|結論|最後に|振り返り/i.test(label)) return 'summary';
            if(/注意|危険|副作用|禁忌|リスク|受診|警告|避ける|デメリット/i.test(label)) return 'caution';
            return index<0?'normal':'explain';
          }
          function update() {
            ticking=false;
            if(!mobile.matches) {
              var rect=content.getBoundingClientRect();
              var gap=Math.round(rect.left);
              var enough=gap>=195 && window.innerWidth>=1050;
              var visible=enough && rect.bottom>100 && rect.top<window.innerHeight-50;
              panel.classList.toggle('s40-visible',visible);
              if(!visible) return;
              panel.style.left=Math.max(8,Math.round(gap-183))+'px';
            } else {
              panel.classList.add('s40-visible');
              panel.style.left='';
            }
            var index=-1;
            for(var i=0;i<headings.length;i++) {
              if(headings[i].getBoundingClientRect().top < window.innerHeight*.43) index=i;
            }
            var h=index>=0?headings[index]:null;
            var key=classify(h,index);
            if(active!==key) {
              active=key;
              if(paths[key]) { img.src=paths[key]; }
            }
            var title=h?(h.textContent||'').trim().replace(/\s+/g,' '):'';
            var prefix=key==='caution'?'ここは注意して確認しましょう。':key==='summary'?'最後に要点を整理します。':key==='normal'?'この記事のポイントをご案内します。':'いまのテーマはこちら。';
            var message=(key==='normal' || !title)?prefix:prefix+'「'+title.slice(0,32)+'」';
            if(txt.textContent!==message) txt.textContent=message;
          }
          function request() { if(ticking)return; ticking=true; requestAnimationFrame(update); }
          if(mobile.matches) content.insertBefore(panel,content.firstChild);
          window.addEventListener('scroll',request,{passive:true});
          window.addEventListener('resize',request,{passive:true});
          if(mobile.addEventListener) mobile.addEventListener('change',function(){
            if(mobile.matches) content.insertBefore(panel,content.firstChild);
            else document.body.appendChild(panel);
            request();
          });
          request();
        })();
        </script>
        <?php
    }

'''
s=s.replace(anchor,method+anchor,1)
p.write_text(s,encoding="utf-8")
print("navigator patch applied for "+version)
