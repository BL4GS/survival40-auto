"""STAGED ONLY. Not connected to release.yml to avoid another automatic deployment
before the WordPress plugin deactivation issue is diagnosed.
Run after patch_author_update_stability_01920.py, with explicit release approval.
"""
from pathlib import Path
p=Path("survival40-auto/survival40-auto.php")
s=p.read_text(encoding="utf-8")
needle="            ['id'=>'aono','name'=>'マンダム aono'"
assert s.count(needle)==1, "Expected existing A8 seed was not found"
insert="""            ['id'=>'s00000015223035','name'=>'ハウスクリーニング110番','category'=>'住まい・季節の掃除','reward'=>'新規見積依頼1,300円','status'=>'approved','notes'=>'WEB・電話申込後30日以内の加盟店手配完了が成果条件。重複、同一世帯2回以上の申込、SNSの連投誘導は否認対象。EPC 1.77、確定率33.33%。'],
            ['id'=>'s00000022315001','name'=>'SharkNinja公式ストア','category'=>'家電・家事効率化','reward'=>'購入2%','status'=>'approved','notes'=>'WEB注文後決済完了。アクセサリー・アウトレット商品のみの購入は対象外。提供素材以外の無断利用禁止。EPC 9.66、確定率59.32%。'],
            ['id'=>'s00000026776002','name'=>'RingConn 第2世代','category'=>'睡眠・健康管理','reward'=>'購入7%','status'=>'approved','notes'=>'対象はLP掲載の第2世代のみ。WEB注文後30日以内の入金確認。LINE経由購入は対象外。価格・機能・機種世代の誤記禁止。'],
"""
s=s.replace(needle,insert+needle,1)
anchor="    public function s40_affiliate_ledger_menu() {"
assert s.count(anchor)==1
# This matching method is inert until a separately reviewed publishing integration
# calls it. Explicit mapping avoids unsafe generic keyword-based ad insertion.
method="""    private function s40_affiliate_match_preview($article_topic) {
        $mapped = [
            'aircon-cleaning' => ['s00000015223035'],
            'cordless-vacuum' => ['s00000022315001'],
            'sleep-tracking' => ['s00000026776002'],
        ];
        if (!isset($mapped[$article_topic])) return [];
        $ledger = $this->s40_affiliate_ledger_get();
        $candidates = [];
        foreach ($mapped[$article_topic] as $id) {
            if (!isset($ledger[$id])) continue;
            $row = $ledger[$id];
            if ($row['status'] !== 'approved') continue;
            if (empty($row['url']) || !wp_http_validate_url($row['url'])) continue;
            if (strpos($row['url'], 'https://') !== 0) continue;
            // The caller must separately verify the exact item, link rules,
            // PR disclosure, and article accuracy before publication.
            $candidates[] = $row;
        }
        return $candidates;
    }

"""
s=s.replace(anchor,method+anchor,1)
p.write_text(s,encoding="utf-8")
print("staged 3 ledger rows and guarded matching preview; nothing auto-publishes")
