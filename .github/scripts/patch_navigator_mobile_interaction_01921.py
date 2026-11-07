"""Stage mobile tap-to-show Shiori guide, no WordPress changes or release.

Apply on reconstructed plugin PHP after patch_navigator_mobile_lead_01921.py.
The mobile-only control does not alter desktop navigator or editorial scripts.
"""
from pathlib import Path

SOURCE = Path("survival40-auto/survival40-auto.php")


def once(source, old, new):
    if source.count(old) != 1:
        raise ValueError("Expected exactly one UI patch anchor: " + old[:90])
    return source.replace(old, new, 1)


CSS = r"""          /* Mobile Shiori: keep a small avatar, expand guidance only as needed.
             These selectors deliberately outrank saved Additional CSS. */
          .s40-presenter-toggle, .s40-presenter-dismiss { display:none; }
          @media (max-width:850px) {
            html body.single-post #s40-presenter.s40-visible {
              position:fixed !important; top:auto !important;
              left:auto !important; right:12px !important;
              bottom:calc(76px + env(safe-area-inset-bottom,0px)) !important;
              margin:0 !important; padding:0 !important;
              width:min(310px,calc(100vw - 24px)) !important;
              max-width:calc(100vw - 24px) !important;
              display:flex !important; align-items:flex-end !important;
              gap:8px !important; flex-direction:row !important;
              z-index:80 !important; pointer-events:none !important;
            }
            html body.single-post #s40-presenter.s40-visible.s40-collapsed {
              display:block !important; width:52px !important;
              max-width:52px !important;
            }
            html body.single-post #s40-presenter .s40-presenter-image {
              order:2; flex:0 0 52px !important;
              width:52px !important; height:72px !important;
              max-height:72px !important; object-fit:contain !important;
              object-position:bottom !important;
            }
            html body.single-post #s40-presenter .s40-presenter-caption {
              order:1; position:relative !important; flex:1 1 auto !important;
              min-width:0 !important; max-height:82px !important;
              margin:0 !important; padding:7px 26px 7px 10px !important;
              background:rgba(248,248,255,.98) !important;
              border-radius:10px !important; overflow:hidden !important;
            }
            html body.single-post #s40-presenter.s40-collapsed .s40-presenter-caption {
              display:none !important;
            }
            html body.single-post #s40-presenter .s40-presenter-toggle {
              display:block !important; position:absolute !important;
              right:0 !important; bottom:0 !important; width:52px !important;
              height:72px !important; padding:0 !important; margin:0 !important;
              border:0 !important; border-radius:8px !important;
              background:transparent !important; cursor:pointer !important;
              pointer-events:auto !important; z-index:3 !important;
            }
            html body.single-post #s40-presenter .s40-presenter-dismiss {
              display:block !important; position:absolute !important;
              right:2px !important; top:1px !important;
              width:24px !important; height:24px !important;
              line-height:24px !important; font-size:17px !important;
              border:0 !important; padding:0 !important;
              background:transparent !important; color:#334 !important;
              cursor:pointer !important; pointer-events:auto !important;
              z-index:4 !important;
            }
            html body.single-post #s40-presenter .s40-presenter-toggle:focus-visible,
            html body.single-post #s40-presenter .s40-presenter-dismiss:focus-visible {
              outline:2px solid #4059e9 !important; outline-offset:2px !important;
            }
          }
"""

BEFORE_HTML = """            <span class="s40-presenter-text">この記事のポイントをご案内します。</span>
          </div>
        </aside>"""
AFTER_HTML = """            <span class="s40-presenter-text" id="s40-presenter-message">この記事のポイントをご案内します。</span>
            <button type="button" class="s40-presenter-dismiss" aria-label="栞さんの案内をこのページで閉じる">×</button>
          </div>
          <button type="button" class="s40-presenter-toggle" aria-label="栞さんの案内を表示" aria-controls="s40-presenter-message" aria-expanded="false" title="栞さんの案内を表示"></button>
        </aside>"""

AFTER_VARIABLES = """          var toggle=panel.querySelector('.s40-presenter-toggle');
          var dismiss=panel.querySelector('.s40-presenter-dismiss');
          var dismissed=false;
          var expanded=false;
          var pinnedOpen=false;
          var hideTimer=null;
          var lastHeadingIndex=null;
          function expandMobile(show) {
            if(!mobile.matches || dismissed) return;
            expanded=!!show;
            panel.classList.toggle('s40-collapsed',!expanded);
            toggle.setAttribute('aria-expanded',expanded?'true':'false');
            toggle.setAttribute('aria-label',expanded?'栞さんの案内を隠す':'栞さんの案内を表示');
            toggle.title=expanded?'栞さんの案内を隠す':'栞さんの案内を表示';
          }
          function showBriefly() {
            if(!mobile.matches || dismissed || pinnedOpen) return;
            if(hideTimer!==null) window.clearTimeout(hideTimer);
            expandMobile(true);
            hideTimer=window.setTimeout(function() {
              hideTimer=null;
              if(!pinnedOpen) expandMobile(false);
            },4000);
          }
          toggle.addEventListener('click',function() {
            if(!mobile.matches || dismissed) return;
            if(hideTimer!==null) { window.clearTimeout(hideTimer); hideTimer=null; }
            pinnedOpen=!expanded;
            expandMobile(!expanded);
          });
          dismiss.addEventListener('click',function() {
            if(!mobile.matches) return;
            dismissed=true;
            pinnedOpen=false;
            if(hideTimer!==null) {window.clearTimeout(hideTimer);hideTimer=null;}
            panel.classList.remove('s40-visible');
            toggle.setAttribute('aria-expanded','false');
          });
"""

def apply(source):
    source=once(source,
        "        </style>\n        <aside id=\"s40-presenter\"",
        CSS+"        </style>\n        <aside id=\"s40-presenter\"")
    source=once(source, BEFORE_HTML, AFTER_HTML)
    source=once(source,
        "          var txt=panel.querySelector('.s40-presenter-text');\n",
        "          var txt=panel.querySelector('.s40-presenter-text');\n")
    anchor="          var mobile=window.matchMedia('(max-width:850px)');\n"
    source=once(source,anchor,anchor+AFTER_VARIABLES)
    mobile_block="""            } else {
              panel.classList.add('s40-visible');
              panel.style.left='';
            }"""
    changed_mobile="""            } else {
              if(dismissed) {panel.classList.remove('s40-visible');return;}
              panel.classList.add('s40-visible');
              panel.style.left='';
            }"""
    source=once(source,mobile_block,changed_mobile)
    replace="""            var h=index>=0?headings[index]:null;"""
    source=once(source,replace,
        """            if(mobile.matches && lastHeadingIndex!==index) {
              lastHeadingIndex=index;
              showBriefly();
            }
            var h=index>=0?headings[index]:null;""")
    anchor="""          if(mobile.matches) content.insertBefore(panel,content.firstChild);
          window.addEventListener('scroll',request,{passive:true});"""
    source=once(source,anchor,
        """          if(mobile.matches) {
            content.insertBefore(panel,content.firstChild);
            expandMobile(false);
          }
          window.addEventListener('scroll',request,{passive:true});""")
    anchor="""            if(mobile.matches) content.insertBefore(panel,content.firstChild);
            else document.body.appendChild(panel);
            request();"""
    source=once(source,anchor,
        """            if(mobile.matches) {
              content.insertBefore(panel,content.firstChild);
              lastHeadingIndex=null;
              expandMobile(false);
            } else {
              document.body.appendChild(panel);
              panel.classList.remove('s40-collapsed');
              if(hideTimer!==null) {window.clearTimeout(hideTimer);hideTimer=null;}
            }
            request();""")
    if source.count("function showBriefly()")!=1:
        raise ValueError("Missing interaction function")
    if source.count('Math.min(window.innerHeight*.72,580)')!=1:
        raise ValueError("Required early mobile heading trigger not installed")
    return source


if __name__=="__main__":
    src=SOURCE.read_text(encoding="utf-8")
    dst=apply(src)
    assert dst!=src
    SOURCE.write_text(dst,encoding="utf-8")
    print("PASS: Shiori mobile tap-to-open, auto-collapse and article-only dismiss staged")
