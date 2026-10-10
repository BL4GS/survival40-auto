"""Staging-only: prepare a reviewed, opt-in post banner renderer. Never modify release workflow here."""
from pathlib import Path
p=Path("survival40-auto/survival40-auto.php")
s=p.read_text(encoding="utf-8")
anchor="    public function s40_affiliate_ledger_menu() {"
assert s.count(anchor)==1
method=r'''    // Manual opt-in via explicit post meta only. Not an automatic posting hook.
    private function s40_ad_markup_for_post($post_id) {
        if (get_post_meta($post_id, '_s40_affiliate_disabled', true)) return '';
        $topic = (string) get_post_meta($post_id, '_s40_affiliate_topic', true);
        if ($topic === '') return '';
        $matches = $this->s40_affiliate_match_preview($topic);
        if (!$matches) return '';
        // Advertiser-specific editorial and campaign verification is required.
        if (get_post_meta($post_id, '_s40_affiliate_reviewed', true) !== 'yes') return '';
        $row = $matches[0];
        $c = $row['creative'];
        $url = $c['click_url'];
        $img = $c['banner_src'];
        $pixel = $c['impression_src'];
        if (!preg_match('~^https://px\.a8\.net/svt/ejp\?a8mat=[A-Za-z0-9+]+$~D', $url)) return '';
        if (!preg_match('~^https://www[0-9]+\.a8\.net/svt/bgt\?~', $img)) return '';
        if (!preg_match('~^https://www[0-9]+\.a8\.net/0\.gif\?a8mat=~', $pixel)) return '';
        $name = $row['name'];
        return '<aside class="s40-affiliate-banner" aria-label="広告"><p>PR・広告</p>'.
               '<a href="'.esc_url($url).'" rel="nofollow sponsored" target="_blank">'.
               '<img src="'.esc_url($img).'" width="300" height="250" alt="'.esc_attr($name).' の広告" loading="lazy"></a>'.
               '<img src="'.esc_url($pixel).'" width="1" height="1" alt="" aria-hidden="true">'.
               '</aside>';
    }

    // A distinct call site can use this after explicit editorial sign-off.
    // This file intentionally adds no frontend hooks: rollout remains disabled.
'''
s=s.replace(anchor,method+anchor,1)
p.write_text(s,encoding="utf-8")
print("review-gated ad markup renderer staged; no public hook, no release")
