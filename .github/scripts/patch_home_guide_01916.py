from pathlib import Path
import re
p=Path("survival40-auto/survival40-auto.php")
s=p.read_text(encoding="utf-8")
hook="        add_action('wp_footer', [$this, 'survival40_presenter_render'], 50);"
assert s.count(hook)==1
s=s.replace(hook,hook+"\n        add_filter('the_content', [$this, 'survival40_home_guide'], 8);",1)
anchor="    public function survival40_presenter_render() {"
assert s.count(anchor)==1
method=r'''    public function survival40_home_guide($content) {
        if (is_admin() || !is_front_page() || !is_main_query() || !in_the_loop() || is_feed()) {
            return $content;
        }
        $photo = plugin_dir_url(__FILE__) . 'assets/navigator/normal.webp';
        $month = (int) wp_date('n');
        $season = ($month >= 6 && $month <= 8) ? 'summer' : (($month >= 12 || $month <= 2) ? 'winter' : (($month >= 3 && $month <= 5) ? 'spring' : 'autumn'));
        $greetings = [
            'こんにちは、栞です。気になるテーマから、無理なく整えていきましょう。',
            'はじめまして。Survival40ナビゲーターの栞です。今日もできることから、一緒に確認していきましょう。',
            'おかえりなさい。栞です。気になることがあれば、6つのテーマから探してみてください。',
            '見た目も生活も、全部を一度に変えなくて大丈夫。気になるところから始めましょう。',
            'こんにちは、栞です。今日は肌、髪、体型、それとも生活習慣？ 気になるところからどうぞ。',
        ];
        $seasonal = [
            'spring' => ['紫外線が気になり始める季節ですね。日焼け対策の記事も覗いてみませんか？', '新しい季節です。毎日の身だしなみも、少しずつ見直してみましょう。'],
            'summer' => ['暑い季節ですね。汗やニオイのケア、できることから整えていきましょう。', '日差しの強い日が続きますね。日焼け止めの使い方も確認してみませんか？'],
            'autumn' => ['季節の変わり目ですね。肌や生活習慣の見直しに、気になる記事からどうぞ。', '少しずつ乾燥が気になる頃ですね。保湿の基本も確認してみましょう。'],
            'winter' => ['乾燥しやすい季節ですね。肌の保湿から見直してみませんか？', '寒い日が続きますね。無理なく続けられる運動の記事もありますよ。'],
        ];
        $all = array_merge($greetings, $seasonal[$season]);
        $json = wp_json_encode(array_values($all), JSON_UNESCAPED_UNICODE | JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT);
        ob_start();
        ?>
        <style id="s40-home-guide-style">
        .s40-home-guide{display:flex;align-items:center;gap:clamp(15px,3vw,32px);
          margin:20px auto 30px;padding:14px clamp(14px,3vw,30px) 12px;
          max-width:1040px;background:#f8f8ff;border:1px solid #e8e8f3;border-radius:16px;
          box-shadow:0 6px 24px rgba(25,34,65,.04);box-sizing:border-box}
        .s40-home-guide img{width:clamp(105px,18vw,170px);max-height:220px;object-fit:contain;object-position:bottom;align-self:end;flex-shrink:0}
        .s40-home-guide-body{flex:1;min-width:0}
        .s40-home-guide-label{display:block;color:#657088;font-size:11px;letter-spacing:.08em;margin:0 0 5px}
        .s40-home-guide-title{display:block;color:#262e3d;font-size:clamp(17px,2.5vw,23px);font-weight:700;margin:0 0 10px;line-height:1.5}
        .s40-home-guide-message{margin:0;color:#354053;font-size:clamp(13px,1.6vw,15px);line-height:1.9}
        @media(max-width:600px){.s40-home-guide{gap:10px;padding:11px 12px;margin:14px auto 22px}
        .s40-home-guide img{width:95px;max-height:160px}.s40-home-guide-title{font-size:17px}}
        </style>
        <section class="s40-home-guide" aria-label="Survival40ナビゲーター 栞のご案内">
          <img src="<?php echo esc_url($photo); ?>" width="170" height="220" loading="lazy" decoding="async" alt="ナビゲーターの栞" />
          <div class="s40-home-guide-body">
            <span class="s40-home-guide-label">SURVIVAL40 NAVIGATOR</span>
            <span class="s40-home-guide-title">ナビゲーターの栞です。</span>
            <p class="s40-home-guide-message">気になるテーマから、無理なく整えていきましょう。</p>
          </div>
        </section>
        <script>
        (function(){var el=document.querySelector('.s40-home-guide-message');
          if(!el)return;
          var choices=<?php echo $json; ?>;
          if(choices&&choices.length)el.textContent=choices[Math.floor(Math.random()*choices.length)];
        })();
        </script>
        <?php
        return ob_get_clean() . $content;
    }

'''
s=s.replace(anchor,method+anchor,1)
s,a=re.subn(r"(?m)^(\s*\*\s*Version:\s*)0\.19\.15\s*$",r"\g<1>0.19.16",s,count=1)
s,b=re.subn(r"(?m)^(\s*const\s+VERSION\s*=\s*')0\.19\.15(';\s*)$",r"\g<1>0.19.16\2",s,count=1)
s,c=re.subn(r"<h1>Survival40 Auto v0\.19\.15</h1>","<h1>Survival40 Auto v0.19.16</h1>",s,count=1)
assert a==b==c==1
p.write_text(s,encoding="utf-8")
print("home navigator with seasonal random greeting added")
