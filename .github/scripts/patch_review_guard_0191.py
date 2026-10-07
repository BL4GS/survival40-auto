from pathlib import Path
import re

php = Path("survival40-auto/survival40-auto.php")
text = php.read_text(encoding="utf-8")

text = text.replace(" * Version: 0.19.0\n", " * Version: 0.19.1\n", 1)
text = text.replace("    const VERSION = '0.19.0';", "    const VERSION = '0.19.1';", 1)
text = text.replace("<h1>Survival40 Auto v0.19.0</h1>", "<h1>Survival40 Auto v0.19.1</h1>", 1)

# Add deterministic structural/evidence checks before the AI editor review.
anchor = "    private function review_generated_article($p, $html, $research) {"
if anchor not in text:
    raise SystemExit("review method anchor not found")

preflight = r'''    private function deterministic_article_checks($p, $html, $research) {
        $issues = [];
        $plain = trim(wp_strip_all_tags($html));

        if (mb_strlen($plain, 'UTF-8') < 1400) {
            $issues[] = '本文が短すぎます。最低限の具体性が不足しています。';
        }

        preg_match_all('/<h2\b[^>]*>.*?<\/h2>/isu', $html, $h2s);
        $h2_count = count($h2s[0] ?? []);
        if ($h2_count < 3 || $h2_count > 6) {
            $issues[] = 'H2構成が3〜6個の範囲に収まっていません。';
        }

        // FAQ must contain actual answers, not question headings only.
        preg_match_all('/<h3\b[^>]*>\s*(?:Q[\.\d\s]*)?([^<]*\?)\s*<\/h3>\s*(.*?)(?=<h[23]\b|$)/isu', $html, $faq_matches, PREG_SET_ORDER);
        $faq_answered = 0;
        foreach ($faq_matches as $m) {
            $answer = trim(wp_strip_all_tags($m[2] ?? ''));
            if (mb_strlen($answer, 'UTF-8') >= 30) $faq_answered++;
            else $issues[] = 'FAQの質問に本文回答がありません: ' . sanitize_text_field($m[1] ?? '');
        }
        if (count($faq_matches) < 2) {
            $issues[] = 'FAQが2問以上ありません。';
        } elseif ($faq_answered < count($faq_matches)) {
            $issues[] = 'FAQの一部が質問だけで終わっています。';
        }

        $source_count = count($research['sources'] ?? []);
        if (!empty($p['ymyl']) && $source_count < 2) {
            $issues[] = 'YMYL記事なのに取得できた根拠資料が2件未満です。';
        }

        // Claims that require a matching evidence theme.
        $ctx = mb_strtolower(wp_strip_all_tags($research['context'] ?? ''), 'UTF-8');
        $article = mb_strtolower($plain, 'UTF-8');

        if ((mb_strpos($article, 'ブルーライト') !== false) &&
            (mb_strpos($ctx, 'ブルーライト') === false && mb_strpos($ctx, 'blue light') === false && mb_strpos($ctx, 'blue-light') === false)) {
            $issues[] = 'ブルーライトに関する主張がありますが、取得資料に対応する根拠が見当たりません。';
        }

        if ((mb_strpos($article, '紫外線') !== false || mb_strpos($article, 'uv') !== false) &&
            (mb_strpos($ctx, '紫外線') === false && mb_strpos($ctx, 'uv') === false && mb_strpos($ctx, 'ultraviolet') === false)) {
            $issues[] = '紫外線・UVに関する主張がありますが、取得資料に対応する根拠が見当たりません。';
        }

        return array_values(array_unique($issues));
    }

'''
text = text.replace(anchor, preflight + anchor, 1)

# Strengthen the AI review prompt and combine it with deterministic checks.
old_start = r'''    private function review_generated_article($p, $html, $research) {
        $prompt =
            "あなたはSurvival40の編集長兼ファクトチェッカーです。\n"'''
new_start = r'''    private function review_generated_article($p, $html, $research) {
        $hard_issues = $this->deterministic_article_checks($p, $html, $research);
        $hard_issue_text = $hard_issues ? ("\n【機械チェックで検出済みの問題】\n- " . implode("\n- ", $hard_issues) . "\n") : '';

        $prompt =
            "あなたはSurvival40の編集長兼ファクトチェッカーです。\n"'''
if old_start not in text:
    raise SystemExit("review start anchor not found")
text = text.replace(old_start, new_start, 1)

old_prompt_tail = r'''. "主題一致、重要事実の裏付け、資料との整合、根拠のない数値・断定・効能、購入誘導による誇張を判定してください。\n"
            . "JSONだけ返すこと。形式: "'''
new_prompt_tail = r'''. "主題一致、重要事実の裏付け、資料との整合、根拠のない数値・断定・効能、購入誘導による誇張を判定してください。\n"
            . "FAQは質問だけで終わっていないか、各質問の直後に30文字以上の実質的な回答があるか必ず確認してください。\n"
            . "記事内で扱う主要論点ごとに、取得済み資料のどれが直接支えているか確認してください。資料にない重要主張が1つでもあればpassにしないでください。\n"
            . "YMYL記事で根拠資料が2件未満ならpassにしないでください。\n"
            . $hard_issue_text
            . "機械チェックで問題が1件でも出ている場合、verdictは必ずrevise、scoreは79以下にしてください。\n"
            . "JSONだけ返すこと。形式: "'''
if old_prompt_tail not in text:
    raise SystemExit("review prompt tail anchor not found")
text = text.replace(old_prompt_tail, new_prompt_tail, 1)

# Force deterministic issues to cap the score/verdict even if Gemini incorrectly returns 100/pass.
old_finalize = r'''        $score = max(0, min(100, intval($data['score'] ?? 0)));
        $data['score'] = $score;
        $data['verdict'] = (($data['verdict'] ?? '') === 'pass' && $score >= 80 && empty($data['source_mismatch'])) ? 'pass' : 'revise';
        return $data;'''
new_finalize = r'''        $score = max(0, min(100, intval($data['score'] ?? 0)));
        if ($hard_issues) {
            $score = min($score, 79);
            $data['issues'] = array_values(array_unique(array_merge($hard_issues, $data['issues'] ?? [])));
            $data['verdict'] = 'revise';
        } else {
            $data['verdict'] = (($data['verdict'] ?? '') === 'pass' && $score >= 80 && empty($data['source_mismatch'])) ? 'pass' : 'revise';
        }
        $data['score'] = $score;
        return $data;'''
if old_finalize not in text:
    raise SystemExit("review finalize anchor not found")
text = text.replace(old_finalize, new_finalize, 1)

# Require enough dynamic evidence for YMYL before considering the article review complete.
old_research_ok = "$research_ok = (($research['mode'] ?? '') === 'dynamic' && count($research['sources'] ?? []) >= 2);"
new_research_ok = "$research_ok = (($research['mode'] ?? '') === 'dynamic' && count($research['sources'] ?? []) >= (!empty($p['ymyl']) ? 2 : 1));"
if old_research_ok in text:
    text = text.replace(old_research_ok, new_research_ok, 1)

php.write_text(text, encoding="utf-8")
print("patched to 0.19.1")
