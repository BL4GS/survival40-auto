from pathlib import Path

php = Path('survival40-auto/survival40-auto.php')
text = php.read_text(encoding='utf-8')

text = text.replace(' * Version: 0.18.6\n', ' * Version: 0.18.7\n', 1)
text = text.replace("    const VERSION = '0.18.6';", "    const VERSION = '0.18.7';", 1)
text = text.replace('<h1>Survival40 Auto v0.18.6</h1>', '<h1>Survival40 Auto v0.18.7</h1>', 1)

# Strengthen editorial rules for eye/blue-light content.
needle = '        . "- 目元化粧品は製品表示の使用部位・使用回数・注意事項を優先し、全製品共通の使い方を断定しない。\\n"'
insert = needle + \
'        . "- ブルーライトカット眼鏡について、PCやスマホのブルーライトが眼疾患を起こす、またはブルーライトカット眼鏡が眼精疲労を改善・予防すると断定しない。現在の比較試験では短期的な眼精疲労軽減に明確な優位性は示されていない。\\n"' + \
'        . "- ブルーライト対策と紫外線対策を同一視しない。屋外の紫外線対策はUVカット表示を確認する話として分ける。\\n"' + \
'        . "- UV400は製品表示の一つとして扱い、万能な品質保証や効果保証として書かない。\\n"' + \
'        . "- ブルーライトカット率が高いほど目に良い、価格が高いほど効果が高い、という序列を作らない。\\n"'
if needle not in text:
    raise SystemExit('eye editorial anchor not found')
text = text.replace(needle, insert, 1)

# Planner should not choose unsupported blue-light-health claims as a sales thesis.
planner_needle = '            . "医療・健康に近い俗称や断定的表現は避け、必要なら正式な概念を併記する。\\n\\n"'
planner_insert = '            . "医療・健康に近い俗称や断定的表現は避け、必要なら正式な概念を併記する。\\n"' + \
'            . "ブルーライトカット眼鏡を『目の疲れ対策』『目を守る』という効能前提の企画にしない。扱う場合はエビデンスを確認する記事、またはUV対策・フィット感など別論点と明確に分ける。\\n\\n"'
if planner_needle in text:
    text = text.replace(planner_needle, planner_insert, 1)

# Front-end typography guard. This avoids theme link styles blowing up affiliate/related links.
hook = "        add_action('admin_init', [$this, 'github_force_refresh_once']);"
hook_new = hook + "\n        add_action('wp_head', [$this, 'front_typography_guard']);"
if hook in text and "front_typography_guard" not in text:
    text = text.replace(hook, hook_new, 1)

method_anchor = "    public function github_force_refresh_once() {"
method = r'''    public function front_typography_guard() {
        if (is_admin()) return;
        echo '<style id="survival40-auto-typography-guard">
        .s40-auto-related a,
        .s40-auto-related li,
        article a[href*="amazon.co.jp"],
        article a[href*="amzn.to"],
        article a[href*="amazon/"],
        .entry-content a[href*="amazon.co.jp"],
        .entry-content a[href*="amzn.to"]{
            font-size:16px !important;
            line-height:1.6 !important;
            font-weight:600 !important;
            display:inline !important;
            word-break:normal !important;
        }
        .s40-auto-related h2{
            font-size:24px !important;
            line-height:1.35 !important;
        }
        .s40-auto-related ul{
            margin-top:8px !important;
            padding-left:22px !important;
        }
        </style>';
    }

'''
if method_anchor in text and "public function front_typography_guard()" not in text:
    text = text.replace(method_anchor, method + method_anchor, 1)

php.write_text(text, encoding='utf-8')
print('patched to 0.18.7')
