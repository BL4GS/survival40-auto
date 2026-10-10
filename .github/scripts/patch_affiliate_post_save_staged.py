"""Staging only: connect affiliate proposals to WordPress post saves, never publish ads."""
from pathlib import Path
p=Path("survival40-auto/survival40-auto.php")
s=p.read_text(encoding="utf-8")
hook="        add_action('admin_menu', [$this, 's40_affiliate_ledger_menu']);"
assert s.count(hook)==1
s=s.replace(hook,hook+"\n        add_action('save_post_post', [$this, 's40_affiliate_on_post_saved'], 20, 3);",1)
anchor="    public function s40_affiliate_ledger_menu() {"
assert s.count(anchor)==1
method=r'''    // Saves proposal IDs only; creates no external links or impressions.
    public function s40_affiliate_on_post_saved($post_id, $post, $update) {
        if (!$post || $post->post_type !== 'post') return;
        if (wp_is_post_revision($post_id) || wp_is_post_autosave($post_id)) return;
        if (!in_array($post->post_status, ['draft','pending','future','publish'], true)) return;
        $topic = (string) get_post_meta($post_id, '_s40_affiliate_topic', true);
        if ($topic === '' || get_post_meta($post_id, '_s40_affiliate_disabled', true)) {
            delete_post_meta($post_id, '_s40_affiliate_proposed_ids');
            return;
        }
        $proposal = $this->s40_affiliate_prepare_review($post_id, $topic);
        $ids = [];
        foreach ($proposal['suggested_ads'] as $candidate) {
            $ids[] = $candidate['id'];
        }
        // Store only safe IDs for human or future automated editorial review.
        if ($ids) update_post_meta($post_id, '_s40_affiliate_proposed_ids', $ids);
        else delete_post_meta($post_id, '_s40_affiliate_proposed_ids');
        // Never set _s40_affiliate_reviewed; never edit post_content or post_status.
    }

'''
s=s.replace(anchor,method+anchor,1)
p.write_text(s,encoding="utf-8")
print("post-save proposal cache staged; no ad insertion, content edits, or publish actions")
