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
# Append a read-only match check on the private ledger screen.
# This adds no scheduled jobs, frontend output, or automatic posting.
preview_anchor="          <?php submit_button('広告台帳を保存'); ?>"
assert s.count(preview_anchor)==1, "Ledger save button anchor changed"
preview="""          <?php submit_button('広告台帳を保存'); ?>
          <h2>記事テーマ別の照合プレビュー（広告は掲載されません）</h2>
          <p>このプレビューは台帳の保存済みURLだけを使います。未登録・審査中の案件は非表示です。記事への自動掲載はまだ有効化していません。</p>
          <table class="widefat striped"><thead><tr><th>記事テーマ</th><th>掲載候補</th><th>状態</th></tr></thead><tbody>
          <?php foreach ([
            'aircon-cleaning'=>'エアコン掃除・業者への依頼',
            'cordless-vacuum'=>'コードレス掃除機選び',
            'sleep-tracking'=>'睡眠データ・スマートリング',
          ] as $topic=>$label):
            $matches = $this->s40_affiliate_match_preview($topic);
          ?>
          <tr><td><?php echo esc_html($label); ?></td>
          <td><?php echo esc_html(implode('、', array_column($matches,'name')) ?: '候補なし'); ?></td>
          <td><?php echo $matches ? '審査・広告表示の個別確認が必要' : 'URL未登録等のため掲載不可'; ?></td></tr>
          <?php endforeach; ?></tbody></table>
"""
s=s.replace(preview_anchor,preview,1)
p.write_text(s,encoding="utf-8")
print("staged 3 ledger rows and guarded matching preview; nothing auto-publishes")
