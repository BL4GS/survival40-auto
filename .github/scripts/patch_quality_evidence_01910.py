from pathlib import Path
import re

p=Path("survival40-auto/survival40-auto.php")
s=p.read_text(encoding="utf-8")
target="0.19.10"

# Version surfaces.
s,n1=re.subn(r"(?m)^(\s*\*\s*Version:\s*)\d+\.\d+\.\d+\s*$",lambda m:m.group(1)+target,s,count=1)
s,n2=re.subn(r"(?m)^(\s*const\s+VERSION\s*=\s*')[^']+(';\s*)$",lambda m:m.group(1)+target+m.group(2),s,count=1)
s,n3=re.subn(r"<h1>Survival40 Auto v\d+\.\d+\.\d+</h1>","<h1>Survival40 Auto v"+target+"</h1>",s,count=1)
if not (n1 and n2 and n3):
    raise SystemExit("version surfaces not found")

# Discovery prompt: relevance before prestige.
s=s.replace(
    '"優先: 日本の省庁・公的機関・専門学会・大学・公的研究機関。製品仕様はメーカー公式一次情報。医学的主張は診療ガイドラインや系統的レビュー。\\n"',
    '"最優先は記事テーマへの直接関連性。権威性が高くても主要論点を直接支えない資料は採用しない。製品の仕様・使い方・適合素材・注意事項はメーカー公式の取扱説明書・FAQ・仕様ページを優先し、健康・医療の主張だけ省庁・専門学会・大学・診療ガイドライン等を優先する。\\n"',
    1
)
s=s.replace(
    '"禁止: アフィリエイトサイト、まとめ、個人ブログ、検索結果URL、記事と関係の薄い資料の数合わせ。\\n"',
    '"禁止: アフィリエイトサイト、まとめ、個人ブログ、検索結果URL、組織トップページ、統計一覧、記事の主要論点を直接説明しない資料、権威性だけを理由にした数合わせ。\\n"',
    1
)

# Add one batched relevance/coverage judge after the source-fetch method.
anchor="    private function research_topic($p) {"
if anchor not in s:
    raise SystemExit("research_topic anchor not found")

helper=r'''    private function research_filter_relevant_sources($p, $candidates) {
        if (!$candidates) return [];

        $blocks = [];
        foreach (array_slice($candidates, 0, 8) as $i => $src) {
            $blocks[] =
                "SOURCE " . $i . "\n"
                . "name: " . ($src['name'] ?? '') . "\n"
                . "url: " . ($src['url'] ?? '') . "\n"
                . "declared role: " . ($src['why'] ?? '') . "\n"
                . "body: " . mb_substr(wp_strip_all_tags($src['text'] ?? ''), 0, 2200, 'UTF-8');
        }

        $prompt =
            "あなたはSurvival40の資料採用担当です。権威性ではなく、記事テーマへの直接関連性と本文で確認できる根拠だけで判定してください。\n"
            . "記事タイトル: {$p['title']}\nキーワード: {$p['keyword']}\nカテゴリ: {$p['category']}\n\n"
            . implode("\n\n", $blocks)
            . "\n\n各SOURCEについて0〜100のrelevance_scoreを付け、記事の主要な選び方・使い方・注意点を本文が直接支える場合だけ75点以上にしてください。"
            . "一般統計、組織トップページ、周辺的な医療情報、テーマ語が偶然含まれるだけの資料は74点以下。"
            . "製品仕様・使用方法の記事ではメーカー公式の取扱説明書・FAQ・仕様が直接根拠になり得ます。"
            . "JSONだけ返すこと。形式: {\"sources\":[{\"index\":0,\"relevance_score\":0,\"supports\":[\"直接支える論点\"],\"reason\":\"理由\"}]}";

        $raw = $this->call_gemini_raw($prompt, 0.0, 2400);
        if (is_wp_error($raw)) return [];
        $raw = trim($raw);
        if (substr($raw, 0, 1) !== '{') {
            $a = strpos($raw, '{'); $b = strrpos($raw, '}');
            if ($a !== false && $b !== false && $b > $a) $raw = substr($raw, $a, $b - $a + 1);
        }
        $data = json_decode($raw, true);
        if (!is_array($data) || empty($data['sources']) || !is_array($data['sources'])) return [];

        $accepted = [];
        foreach ($data['sources'] as $judged) {
            $idx = intval($judged['index'] ?? -1);
            $score = intval($judged['relevance_score'] ?? 0);
            $supports = array_values(array_filter($judged['supports'] ?? [], 'is_string'));
            if ($idx < 0 || !isset($candidates[$idx]) || $score < 75 || !$supports) continue;
            $src = $candidates[$idx];
            $src['relevance_score'] = max(0, min(100, $score));
            $src['supports'] = $supports;
            $src['relevance_reason'] = sanitize_text_field($judged['reason'] ?? '');
            $accepted[] = $src;
        }
        return $accepted;
    }

'''
if "private function research_filter_relevant_sources(" not in s:
    s=s.replace(anchor,helper+anchor,1)

# Replace research_topic wholesale: fetch candidates, then judge direct relevance;
# never pad with generic curated sources.
pat=re.compile(r"    private function research_topic\(\$p\) \{.*?\n    \}\n\n    private function dynamic_source_block",re.S)
m=pat.search(s)
if not m:
    raise SystemExit("research_topic block not found")

new_topic=r'''    private function research_topic($p) {
        $candidates = [];
        $failed = [];

        for ($attempt = 1; $attempt <= 3 && count($candidates) < 8; $attempt++) {
            $discovery = $this->research_discover_sources($p, $failed);
            if (is_wp_error($discovery)) continue;

            foreach ($discovery['sources'] ?? [] as $source) {
                if (count($candidates) >= 8) break;
                $url = isset($source['url']) ? esc_url_raw($source['url']) : '';
                if (!$url) continue;

                $duplicate = false;
                foreach ($candidates as $a) if (($a['url'] ?? '') === $url) { $duplicate = true; break; }
                if ($duplicate) continue;

                $fetched = $this->research_fetch_source($source);
                if ($fetched) $candidates[] = $fetched;
                else $failed[] = $url;
            }
        }

        $accepted = $this->research_filter_relevant_sources($p, $candidates);
        usort($accepted, function($a,$b){
            return intval($b['relevance_score'] ?? 0) <=> intval($a['relevance_score'] ?? 0);
        });
        $accepted = array_slice($accepted, 0, 4);

        if (count($accepted) < 2) {
            $lines = [
                "【調査結果】記事テーマを直接裏付ける資料が2件揃いませんでした。",
                "この状態では公開不可。裏付けのない主張を作らず、下書きとして扱ってください。"
            ];
            foreach ($accepted as $i => $src) {
                $lines[] = "採用資料" . ($i + 1) . ": " . ($src['name'] ?? '') . " " . ($src['url'] ?? '');
            }
            return ['mode'=>'research_failed','sources'=>$accepted,'context'=>implode("\n",$lines)];
        }

        $lines = [];
        foreach ($accepted as $i => $src) {
            $n = $i + 1;
            $lines[] = "【調査資料{$n}】{$src['name']}";
            $lines[] = "URL: {$src['url']}";
            $lines[] = "関連度: " . intval($src['relevance_score'] ?? 0) . "/100";
            if (!empty($src['supports'])) $lines[] = "直接支える論点: " . implode(' / ', $src['supports']);
            if (!empty($src['why'])) $lines[] = "候補時の役割: {$src['why']}";
            $lines[] = "取得本文: {$src['text']}";
            $lines[] = "";
        }
        $lines[] = "【執筆制約】";
        $lines[] = "・40代という年齢だけを理由に、皮脂・視力・疲労・生活行動などの変化を作らない。年齢由来の主張は資料が直接支える場合だけ書く。";
        $lines[] = "・タイトルの検索意図から外れる医療、診断、受診、別商品の選び方へ話を広げない。安全上必要な注意は短く留める。";
        $lines[] = "・取得資料が直接支えない効能、因果関係、数値、推奨を追加しない。";
        return ['mode'=>'dynamic','sources'=>$accepted,'context'=>implode("\n",$lines)];
    }

    private function dynamic_source_block'''
s=s[:m.start()]+new_topic+s[m.end():]

# Generic deterministic evidence gate: not just YMYL.
gate_anchor="""        $source_count = count($research['sources'] ?? []);
        if (!empty($p['ymyl']) && $source_count < 2) {"""
gate_new="""        $source_count = count($research['sources'] ?? []);
        if (($research['mode'] ?? '') !== 'dynamic' || $source_count < 2) {
            $issues[] = '記事テーマを直接裏付ける採用資料が2件未満です。';
        }
        if (!empty($p['ymyl']) && $source_count < 2) {"""
if gate_anchor not in s:
    raise SystemExit("deterministic source-count anchor not found")
s=s.replace(gate_anchor,gate_new,1)

# Reviewer: explicit coverage + age-hook + drift rules. Avoid duplicates if 0.19.7 already added them.
review_marker='            . "FAQは質問だけで終わっていないか、各質問の直後に30文字以上の実質的な回答があるか必ず確認してください。\\n"'
if review_marker in s and "各主要主張について、どの採用資料のどの論点が直接支えるか" not in s:
    addition=review_marker + (
        '            . "各主要主張について、どの採用資料のどの論点が直接支えるか確認し、対応できない重要主張があればunsupported_claimsへ入れてpassにしないでください。\\n"\n'
        '            . "『40代だから』『40代になると』を理由に身体・皮脂・視力・疲労・行動の変化を述べる場合、その年齢差を採用資料が直接支えていなければissuesへ入れてください。\\n"\n'
        '            . "記事タイトルの検索意図と直接関係しない医療・診断・受診・別商品の選び方へ展開した場合はtopic_drift=trueとしてpassにしないでください。\\n"\n'
    )
    s=s.replace(review_marker,addition,1)

# Keep useful relevance metadata for later diagnosis.
old_meta="['name'=>$src['name'] ?? '', 'url'=>$src['url'] ?? '', 'source_type'=>$src['source_type'] ?? '']"
new_meta="['name'=>$src['name'] ?? '', 'url'=>$src['url'] ?? '', 'source_type'=>$src['source_type'] ?? '', 'relevance_score'=>intval($src['relevance_score'] ?? 0), 'supports'=>$src['supports'] ?? []]"
if old_meta in s:
    s=s.replace(old_meta,new_meta,1)

p.write_text(s,encoding="utf-8")
print("quality evidence gate patched to 0.19.10")
