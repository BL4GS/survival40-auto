"""Staging only: enforce review metadata and item-specific A8 campaign constraints."""
from pathlib import Path
p=Path("survival40-auto/survival40-auto.php")
s=p.read_text(encoding="utf-8")
anchor="    public function s40_affiliate_ledger_menu() {"
assert s.count(anchor)==1
method=r'''    // Fail closed: only campaign/item pairs explicitly reviewed for an article may render.
    private function s40_affiliate_eligible_for_post($post_id, $row) {
        if (!is_array($row) || empty($row['id'])) return false;
        if (($row['status'] ?? '') !== 'approved') return false;
        if (get_post_meta($post_id, '_s40_affiliate_disabled', true)) return false;
        if (get_post_meta($post_id, '_s40_affiliate_reviewed', true) !== 'yes') return false;
        $approved_id = (string)get_post_meta($post_id, '_s40_affiliate_reviewed_program_id', true);
        if ($approved_id === '' || $approved_id !== (string)$row['id']) return false;
        if ((string)get_post_meta($post_id, '_s40_affiliate_conditions_verified', true) !== 'yes') return false;
        $id = (string)$row['id'];
        if ($id === 's00000022947002') return false; // advertiser not verified
        $item = (string)get_post_meta($post_id, '_s40_affiliate_item_code', true);
        // Exact LP product restrictions require explicit selection, not just topic matches.
        $restricted = [
            's00000014286004'=>['all-in-one-gel'],
            's00000020317006'=>['protect-moisture-uv'],
            's00000026776002'=>['ringconn-gen2'],
        ];
        if (isset($restricted[$id]) && !in_array($item, $restricted[$id], true)) return false;
        return true;
    }

'''
s=s.replace(anchor,method+anchor,1)
line="        $row = $matches[0];"
assert s.count(line)==1
s=s.replace(line,"        $row = $matches[0];\n        if (!$this->s40_affiliate_eligible_for_post($post_id, $row)) return '';",1)
p.write_text(s,encoding="utf-8")
print("staged article/campaign/item review gate; display remains disconnected")
