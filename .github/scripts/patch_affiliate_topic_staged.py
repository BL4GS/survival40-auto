"""Staging only: conservative Japanese topic inference for ads, never automatic approval."""
from pathlib import Path
p=Path("survival40-auto/survival40-auto.php")
s=p.read_text(encoding="utf-8")
anchor="    public function s40_affiliate_ledger_menu() {"
assert s.count(anchor)==1
method=r'''    // Prefer explicit topic meta. Otherwise only high-confidence title matches.
    private function s40_affiliate_infer_topic($post) {
        if (!$post || $post->post_type !== 'post') return '';
        $title = (string)$post->post_title;
        if ($title === '') return '';
        $topics = [
            'protein'=>['プロテイン','ホエイ'],
            'haircare'=>['シャンプー','洗髪'],
            'skincare'=>['日焼け止め','オールインワンジェル'],
            'sleep'=>['枕選び','スマートリング','睡眠トラッキング'],
            'cleaning'=>['ハウスクリーニング','エアコンクリーニング'],
            'vacuum'=>['掃除機','コードレスクリーナー'],
            'meal-delivery'=>['宅配弁当','冷凍宅配食'],
            'bbq'=>['バーベキュー','BBQ'],
            'fashion'=>['メンズファッション','コーディネート'],
            'fitness'=>['加圧シャツ'],
        ];
        $hits = [];
        foreach ($topics as $topic=>$keywords) {
            foreach ($keywords as $word) {
                if (mb_stripos($title, $word, 0, 'UTF-8') !== false) {
                    $hits[$topic] = true;
                    break;
                }
            }
        }
        // Conflicting themes or no clear theme => no proposed advertisement.
        return count($hits) === 1 ? (string)array_key_first($hits) : '';
    }

'''
s=s.replace(anchor,method+anchor,1)
old="        $topic = (string) get_post_meta($post_id, '_s40_affiliate_topic', true);"
assert s.count(old)==2, "Expected one read in banner renderer and one in save hook"
# Only update the save hook (second occurrence); the renderer must require explicit reviewed topic.
start=s.index("    public function s40_affiliate_on_post_saved(")
a=s[:start]
b=s[start:]
assert b.count(old)==1
b=b.replace(old,"        $topic = (string) get_post_meta($post_id, '_s40_affiliate_topic', true);\n        if ($topic === '') $topic = $this->s40_affiliate_infer_topic($post);",1)
s=a+b
p.write_text(s,encoding="utf-8")
print("staged conservative topic inference on save only; display still requires reviewed explicit topic")
