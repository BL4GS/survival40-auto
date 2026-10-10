"""Stage A8 ledger integration after 0.19.20 patch; NEVER included in release workflow automatically."""
import json
from pathlib import Path
p = Path("survival40-auto/survival40-auto.php")
s = p.read_text(encoding="utf-8")
assets = json.loads(Path("planning/a8-banner-assets-unified-2026-10.json").read_text(encoding="utf-8"))["assets"]
assert len(assets)==16 and len({x["program_id"] for x in assets})==16
# Replace only ledger logic; leave existing posts, navigator, homepage and updater untouched.
needle = "    private function s40_affiliate_ledger_get() {"
assert s.count(needle)==1
# A8 program IDs are immutable; the two legacy keys must be resolved without discarding saved overrides.
aliases = {"ultora":"s00000021719001","s0000007191012":"s00000007191012"}
match = {
    "protein":["s00000021719001","s00000024389001"],
    "skincare":["s00000014286004","s00000020317006"],
    "haircare":["s00000007191012"],
    "sleep":["s00000016652002","s00000026776002","s00000022516001"],
    "cleaning":["s00000015223035"],
    "vacuum":["s00000022315001"],
    "meal-delivery":["s00000023792001"],
    "bbq":["s00000019450001"],
    "fashion":["s00000014443001"],
    "fitness":["s00000018173002"],
    "fragrance":["s00000017106008"],
}
# Encode media data as JSON and decode it only when an administrator opens the ledger.
def phpsingle(v):
    return "'" + v.replace("\\","\\\\").replace("'","\\'") + "'"
def php_array_strings(values):
    return "[" + ",".join(phpsingle(x) for x in values) + "]"
def php_dict(mapping):
    return "["+",".join(phpsingle(k)+"=>"+php_array_strings(v) for k,v in mapping.items())+"]"
raw_json=json.dumps(assets,ensure_ascii=False,separators=(",",":"))
# This source file is never published publicly by this staging script.
method = """    private function s40_a8_creatives() {
        $creatives = json_decode(@@JSON@@, true);
        if (!is_array($creatives)) return [];
        $indexed = [];
        foreach ($creatives as $c) {
            if (!isset($c['program_id'])) continue;
            $indexed[$c['program_id']] = $c;
        }
        return $indexed;
    }

    private function s40_affiliate_match_preview($article_topic) {
        $map = @@MAPPING@@;
        if (!isset($map[$article_topic])) return [];
        $rows = $this->s40_affiliate_ledger_get();
        $result = [];
        foreach ($map[$article_topic] as $id) {
            if (!isset($rows[$id])) continue;
            $row = $rows[$id];
            if (($row['status'] ?? '') !== 'approved') continue;
            if (empty($row['creative']) || !is_array($row['creative'])) continue;
            $c = $row['creative'];
            if (($c['click_url'] ?? '') !== ($row['url'] ?? '')) continue;
            if (strpos($row['url'],'https://px.a8.net/svt/ejp?') !== 0) continue;
            if (strpos($c['banner_src'] ?? '', 'https://') !== 0) continue;
            if (strpos($c['impression_src'] ?? '', 'https://') !== 0) continue;
            // Return internal candidates only; no automatic posting or tracking pixels.
            $result[] = $row;
        }
        return $result;
    }

    private function s40_affiliate_ledger_get() {
        $saved = get_option('s40_affiliate_ledger_v1', []);
        if (!is_array($saved)) $saved = [];
        $legacy_aliases = @@ALIASES@@;
        // In-memory alias migration. Never silently rewrite an existing WP option.
        foreach ($legacy_aliases as $old=>$new) {
            if (isset($saved[$old]) && !isset($saved[$new])) $saved[$new] = $saved[$old];
        }
        $seed_rows = $this->s40_affiliate_seed();
        $canonical = [];
        foreach ($seed_rows as $r) {
            if (isset($legacy_aliases[$r['id']])) $r['id'] = $legacy_aliases[$r['id']];
            $canonical[$r['id']] = $r;
        }
        $catalog = $this->s40_a8_creatives();
        foreach ($catalog as $id=>$creative) {
            if (isset($canonical[$id])) continue;
            // Additional approved advertisements, but unknown campaigns remain disabled.
            $is_unverified = ($id === 's00000022947002');
            $canonical[$id] = [
                'id'=>$id, 'name'=>$creative['name'],
                'category'=>'追加提携案件', 'reward'=>'要照合',
                'status'=>$is_unverified ? 'inactive' : 'approved',
                'notes'=>$is_unverified ? '広告主・成果条件の確認待ち。掲載禁止。' : 'ASP=A8。成果条件を広告主LPで確認。'
            ];
        }
        $rows = [];
        foreach ($canonical as $id=>$seed) {
            $extra = isset($saved[$id]) && is_array($saved[$id]) ? $saved[$id] : [];
            $creative = $catalog[$id] ?? null;
            $saved_url = isset($extra['url']) ? trim((string)$extra['url']) : '';\n            $url = $saved_url !== '' ? $saved_url : ($creative['click_url'] ?? '');
            $status = in_array($extra['status'] ?? '', ['approved','pending','inactive'],true)
                ? $extra['status'] : $seed['status'];
            $notes = isset($extra['notes']) ? (string)$extra['notes'] : $seed['notes'];
            $rows[$id] = array_merge($seed, [
                'asp'=> $creative ? 'A8' : 'A8（確認待ち）',
                'url'=>$url, 'status'=>$status, 'notes'=>$notes,
                'creative'=> $creative
            ]);
        }
        return $rows;
    }

"""
# Important: the old seed can contain original aliases; expose canonical keys via get only.
# Remove old matching preview first if previous staging patch was used: not supported here.
assert s.count("    private function s40_affiliate_match_preview(")==0, "Run this file directly after patch 0.19.20, not after old staged matcher."
aliases_php="["+",".join(phpsingle(k)+"=>"+phpsingle(v) for k,v in aliases.items())+"]"
method=method.replace("@@JSON@@",phpsingle(raw_json)).replace("@@MAPPING@@",php_dict(match)).replace("@@ALIASES@@",aliases_php)
start=s.index(needle)
end=s.index("    public function s40_affiliate_ledger_menu() {",start)
s=s[:start]+method+s[end:]
# Explicitly disallow an unverified cleaning campaign even if status is edited.
s=s.replace("            if (($row['status'] ?? '') !== 'approved') continue;",
            "            if ($id === 's00000022947002') continue;\n            if (($row['status'] ?? '') !== 'approved') continue;",1)
# Add a private, read-only topic/advertiser preview. An admin view must not fire tracking beacons.
anchor = "          <?php submit_button('広告台帳を保存'); ?>"
assert s.count(anchor)==1
preview = """          <?php submit_button('広告台帳を保存'); ?>
          <h2>テーマ別広告候補（確認用・自動掲載なし）</h2>
          <p>広告候補は編集画面内だけで計算します。広告画像と計測ピクセルはここでは読み込みません。</p>
          <table class="widefat striped"><thead><tr><th>記事テーマ</th><th>広告候補</th></tr></thead><tbody>
          <?php foreach ([
            'protein'=>'プロテイン・栄養','skincare'=>'スキンケア・紫外線対策',
            'haircare'=>'ヘアケア','sleep'=>'睡眠・寝具',
            'cleaning'=>'ハウスクリーニング','vacuum'=>'掃除機',
            'meal-delivery'=>'宅配食','bbq'=>'BBQ','fashion'=>'ファッション',
            'fitness'=>'筋トレ用品','fragrance'=>'身だしなみ・香り'
          ] as $topic=>$label):
            $matches = $this->s40_affiliate_match_preview($topic); ?>
            <tr><td><?php echo esc_html($label); ?></td><td><?php
              echo esc_html($matches ? implode('、', array_column($matches,'name')) : '候補なし');
            ?></td></tr>
          <?php endforeach; ?></tbody></table>
"""
s = s.replace(anchor, preview, 1)
p.write_text(s,encoding="utf-8")
print("16 creatives staged, canonical aliases retained, guarded thematic preview; no frontend hooks")
