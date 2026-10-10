"""Staging-only reviewed banner attachment. Global switch defaults OFF; never touch release workflow."""
from pathlib import Path
p=Path("survival40-auto/survival40-auto.php")
s=p.read_text(encoding="utf-8")
anchor="    public function s40_affiliate_ledger_menu() {"
assert s.count(anchor)==1
method=r'''    // Public display requires a deliberate rollout switch AND article-level review.
    public function s40_affiliate_append_reviewed_banner($content) {
        if (get_option('s40_affiliate_frontend_enabled', 'no') !== 'yes') return $content;
        if (is_admin() || is_feed() || !is_singular('post') || !in_the_loop() || !is_main_query()) return $content;
        $post_id = get_the_ID();
        if (!$post_id || get_post_status($post_id) !== 'publish') return $content;
        $banner = $this->s40_ad_markup_for_post($post_id);
        if ($banner === '') return $content;
        return $content . "\n" . $banner;
    }

'''
s=s.replace(anchor,method+anchor,1)
# Only this reviewed banner uses the content filter; all other article rendering untouched.
hook="        add_filter('the_content', array($this, 's40_affiliate_append_reviewed_banner'), 99);"
# Attach to known class constructor by insertion adjacent to an existing hook added in staged post-save patch.
needle="        add_action('save_post_post', array($this, 's40_affiliate_on_post_saved'), 20, 3);"
assert s.count(needle)==1
s=s.replace(needle, needle+"\n"+hook,1)
p.write_text(s, encoding="utf-8")
print("staged guarded frontend renderer installed with global switch OFF")
