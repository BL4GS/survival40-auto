from pathlib import Path
import re

p=Path("survival40-auto/survival40-auto.php")
s=p.read_text(encoding="utf-8")
target="0.19.7"
s,n1=re.subn(r"(?m)^(\s*\*\s*Version:\s*)\d+\.\d+\.\d+\s*$",lambda m:m.group(1)+target,s,count=1)
s,n2=re.subn(r"(?m)^(\s*const\s+VERSION\s*=\s*')[^']+(';\s*)$",lambda m:m.group(1)+target+m.group(2),s,count=1)
s,n3=re.subn(r"Survival40 Auto v\d+\.\d+\.\d+","Survival40 Auto v"+target,s,count=1)
if n1!=1 or n2!=1 or n3!=1: raise SystemExit("version patch failed")

# Discovery: relevance comes before authority. Prevent generic authoritative pages
# from being used merely because they look trustworthy.
old='''            . "優先: 日本の省庁・公的機関・専門学会・大学・公的研究機関。製品仕様はメーカー公式一次情報。医学的主張は診療ガイドラインや系統的レビュー。\\n"
            . "禁止: アフィリエイトサイト、まとめ、個人ブログ、検索結果URL、記事と関係の薄い資料の数合わせ。\\n"
            . "主要論点を直接支える個別ページURLを2〜5件返すこと。\\n"'''
new='''            . "最優先条件は記事テーマとの直接関連性です。権威性が高くても主要論点を直接支えない資料は返さないでください。\\n"
            . "製品の使い方・適合素材・洗浄時間・洗剤可否などはメーカー公式の取扱説明書・FAQ・仕様ページを優先。健康・医療の主張だけ、省庁・専門学会・大学・診療ガイドライン等を優先してください。\\n"
            . "禁止: アフィリエイトサイト、まとめ、個人ブログ、検索結果URL、トップページ、統計一覧など記事の主要論点を直接説明していない資料、権威性だけを理由にした数合わせ。\\n"
            . "主要論点を直接支える個別ページURLを2〜5件返すこと。whyには、その資料本文で確認できる具体的な根拠を記載してください。\\n"'''
if old not in s: raise SystemExit("discovery prompt anchor not found")
s=s.replace(old,new,1)

# Add a post-fetch semantic relevance gate. This examines the text actually fetched,
# not just Gemini's search-result description.
anchor="    private function research_topic($p) {"
if anchor not in s: raise SystemExit("research_topic anchor not found")
method=r'''    private function research_source_relevance($p, $source) {
        $excerpt = mb_substr(wp_strip_all_tags($source['text'] ?? ''), 0, 5000, 'UTF-8');
        if (!$excerpt) return ['relevant'=>false, 'reason'=>'本文を取得できませんでした'];

        $prompt =
            "あなたは記事資料の採用判定者です。権威性ではなく、記事テーマへの直接関連性だけを厳格に判定してください。\n"
            . "記事タイトル: {$p['title']}\nキーワード: {$p['keyword']}\n"
            . "資料名: " . ($source['name'] ?? '') . "\nURL: " . ($source['url'] ?? '') . "\n"
            . "資料本文抜粋:\n{$excerpt}\n\n"
            . "記事の主要な選び方・使い方・注意点の少なくとも1つを、この資料本文が直接裏付けている場合だけrelevant=true。"
            . "一般的な統計、組織トップページ、テーマと無関係な医療情報、単なる周辺情報はfalse。\n"
            . "JSONだけ返すこと: {\"relevant\":true,\"supports\":[\"直接支える論点\"],\"reason\":\"判定理由\"}";

        $raw=$this->call_gemini_raw($prompt,0.0,1200);
        if (is_wp_error($raw)) return ['relevant'=>false,'reason'=>$raw->get_error_message()];
        $raw=trim($raw);
        if (substr($raw,0,1)!=='{') {
            $a=strpos($raw,'{'); $b=strrpos($raw,'}');
            if ($a!==false && $b!==false && $b>$a) $raw=substr($raw,$a,$b-$a+1);
        }
        $data=json_decode($raw,true);
        if (!is_array($data)) return ['relevant'=>false,'reason'=>'関連性判定の解析失敗'];
        return [
            'relevant'=>!empty($data['relevant']),
            'supports'=>array_values(array_filter($data['supports'] ?? [], 'is_string')),
            'reason'=>sanitize_text_field($data['reason'] ?? ''),
        ];
    }

'''
s=s.replace(anchor,method+anchor,1)

old_fetch='''                $fetched = $this->research_fetch_source($source);
                if ($fetched) $accepted[] = $fetched;
                else $failed[] = $url;'''
new_fetch='''                $fetched = $this->research_fetch_source($source);
                if ($fetched) {
                    $rel = $this->research_source_relevance($p, $fetched);
                    if (!empty($rel['relevant'])) {
                        $fetched['supports'] = $rel['supports'] ?? [];
                        $fetched['relevance_reason'] = $rel['reason'] ?? '';
                        $accepted[] = $fetched;
                    } else {
                        $failed[] = $url;
                    }
                } else {
                    $failed[] = $url;
                }'''
if old_fetch not in s: raise SystemExit("fetch acceptance anchor not found")
s=s.replace(old_fetch,new_fetch,1)

# Do not pad dynamic research with generic curated sources. If direct evidence is
# insufficient, preserve it as research_failed so the article cannot look well-supported.
old_fallback='''        $mode = count($accepted) >= 2 ? 'dynamic' : 'fallback';
        if (count($accepted) < 2) {
            foreach ($this->trusted_sources($p['source_group'] ?? 'general') as $src) {
                if (count($accepted) >= 3) break;
                $accepted[] = [
                    'name' => $src['name'],
                    'url' => $src['url'],
                    'why' => '既存の安全用参考資料',
                    'source_type' => 'curated',
                    'text' => implode(' ', $src['notes'] ?? []),
                ];
            }
        }
        if (!$accepted) return [
            'mode' => 'research_failed',
            'sources' => [],
            'context' => "【調査結果】外部資料を取得できませんでした。この記事は公開不可として下書き保存し、本文では断定を避けてください。",
        ];'''
new_fallback='''        $mode = count($accepted) >= 2 ? 'dynamic' : 'research_failed';
        if (count($accepted) < 2) {
            $lines = ["【調査結果】記事テーマを直接裏付ける資料が2件揃いませんでした。公開不可として下書き保存し、裏付けのない主張は書かないでください。"];
            foreach ($accepted as $i => $src) {
                $lines[] = "採用資料" . ($i + 1) . ": " . ($src['name'] ?? '') . " " . ($src['url'] ?? '');
            }
            return ['mode'=>'research_failed','sources'=>$accepted,'context'=>implode("\n",$lines)];
        }'''
if old_fallback in s:
    s=s.replace(old_fallback,new_fallback,1)
else:
    # 0.19.4 already replaced the fatal empty-research branch; patch the
    # remaining curated fallback independently.
    curated=re.compile(r'''        \$mode = count\(\$accepted\) >= 2 \? 'dynamic' : 'fallback';\n        if \(count\(\$accepted\) < 2\) \{.*?\n        \}''', re.S)
    m=curated.search(s)
    if not m: raise SystemExit("fallback anchor not found")
    s=s[:m.start()]+'''        $mode = count($accepted) >= 2 ? 'dynamic' : 'research_failed';
        if (count($accepted) < 2) {
            $lines = ["【調査結果】記事テーマを直接裏付ける資料が2件揃いませんでした。公開不可として下書き保存し、裏付けのない主張は書かないでください。"];
            foreach ($accepted as $i => $src) {
                $lines[] = "採用資料" . ($i + 1) . ": " . ($src['name'] ?? '') . " " . ($src['url'] ?? '');
            }
            return ['mode'=>'research_failed','sources'=>$accepted,'context'=>implode("\\n",$lines)];
        }'''+s[m.end():]

# Reviewer must reject topic drift and generic age hooks, and verify evidence coverage.
old_review='''            . "記事内で扱う主要論点ごとに、取得済み資料のどれが直接支えているか確認してください。資料にない重要主張が1つでもあればpassにしないでください。\\n"
            . "YMYL記事で根拠資料が2件未満ならpassにしないでください。\\n"'''
new_review='''            . "記事内で扱う主要論点ごとに、取得済み資料のどれが直接支えているか確認してください。資料にない重要主張が1つでもあればpassにしないでください。\\n"
            . "タイトルの主題から外れる節（例: 商品選びの記事で必要性の薄い診断・受診・別商品の選び方へ展開する等）があればtopic_drift=trueとしてpassにしないでください。\\n"
            . "『40代だから○○が増える・変化する』など年齢を理由にした導入は、資料で直接裏付けられない限り問題としてissuesに入れてください。40代向けであること自体を根拠のない身体変化で正当化しないでください。\\n"
            . "取得資料が記事タイトルの主要論点に直接関連していない、または直接関連資料が2件未満ならscoreは79以下、verdictはreviseにしてください。\\n"
            . "YMYL記事で根拠資料が2件未満ならpassにしないでください。\\n"'''
if old_review not in s: raise SystemExit("review prompt anchor not found")
s=s.replace(old_review,new_review,1)

# Enforce topic_drift too; previously it could still pass if Gemini returned pass/80+.
old_verdict="(($data['verdict'] ?? '') === 'pass' && $score >= 80 && empty($data['source_mismatch'])) ? 'pass' : 'revise'"
new_verdict="(($data['verdict'] ?? '') === 'pass' && $score >= 80 && empty($data['source_mismatch']) && empty($data['topic_drift'])) ? 'pass' : 'revise'"
s=s.replace(old_verdict,new_verdict)

p.write_text(s,encoding="utf-8")
print("patched to 0.19.7")
