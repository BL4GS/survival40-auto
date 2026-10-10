"""Staging-only reviewed affiliate proposal integration; no publication side effects."""
from pathlib import Path
p=Path("survival40-auto/survival40-auto.php")
s=p.read_text(encoding="utf-8")
anchor="    public function s40_affiliate_ledger_menu() {"
assert s.count(anchor)==1
method=r'''    // Compute a proposal only, keeping article generation and publishing untouched.
    private function s40_affiliate_propose_for_post($post_id, $topic) {
        $post = get_post($post_id);
        if (!$post || $post->post_type !== 'post') return [];
        if (get_post_meta($post_id, '_s40_affiliate_disabled', true)) return [];
        $valid_topics = [
            'protein','skincare','haircare','sleep','cleaning','vacuum',
            'meal-delivery','bbq','fashion','fitness','fragrance'
        ];
        if (!in_array($topic, $valid_topics, true)) return [];
        $matches = $this->s40_affiliate_match_preview($topic);
        if (!$matches) return [];
        $result = [];
        foreach ($matches as $row) {
            $result[] = ['id'=>$row['id'], 'name'=>$row['name'], 'topic'=>$topic];
        }
        return $result;
    }

    // This method can be called by the editorial review workflow after generation.
    // It never publishes, saves meta, or sends ad tracking beacons.
    private function s40_affiliate_prepare_review($post_id, $topic) {
        return [
            'post_id'=>(int)$post_id,
            'suggested_ads'=>$this->s40_affiliate_propose_for_post($post_id,$topic),
            'manual_review_required'=>true,
            'auto_insert_enabled'=>false,
        ];
    }

'''
s=s.replace(anchor,method+anchor,1)
p.write_text(s,encoding="utf-8")
print("staged review proposal bridge; no publication or saved post changes")
