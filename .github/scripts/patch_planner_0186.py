from pathlib import Path

php = Path('survival40-auto/survival40-auto.php')
text = php.read_text(encoding='utf-8')
text = text.replace(' * Version: 0.18.5\n', ' * Version: 0.18.6\n', 1)
text = text.replace("    const VERSION = '0.18.5';", "    const VERSION = '0.18.6';", 1)
text = text.replace('<h1>Survival40 Auto v0.18.5</h1>', '<h1>Survival40 Auto v0.18.6</h1>', 1)

old = r'''        $raw = $this->call_gemini_raw($prompt, 0.35, 1800);
        if (is_wp_error($raw)) return $raw;

        $data = json_decode($raw, true);
        if (!is_array($data)) {
            $raw = preg_replace('/^```(?:json)?\\s*|\\s*```$/i', '', $raw);
            $data = json_decode($raw, true);
        }
        if (!is_array($data)) return new WP_Error('planner_json', '記事企画JSONの解析に失敗しました。');

        foreach (['title','keyword','category','excerpt','seo_title'] as $k) {
            if (empty($data[$k])) return new WP_Error('planner_missing', '記事企画に必要な項目が不足しています: ' . $k);
        }

        $map = $this->auto_category_map();
        if (!isset($map[$data['category']])) return new WP_Error('planner_category', '記事企画のカテゴリが不正です。');

        $title = sanitize_text_field($data['title']);
        foreach ($titles as $existing_title) {
            if ($this->normalize_title_key($existing_title) === $this->normalize_title_key($title)) {
                return new WP_Error('planner_duplicate', '既存記事と同一タイトルの企画が返されたため保留しました。');
            }
        }

        $cfg = $map[$data['category']];'''

new = r'''        $map = $this->auto_category_map();
        $data = null;
        $last_raw = '';
        $planner_error = '';

        for ($attempt = 1; $attempt <= 3; $attempt++) {
            $attempt_prompt = $prompt;
            if ($attempt > 1) {
                $attempt_prompt .= "\n\n前回の返答は不完全でした。title / keyword / category / excerpt / seo_title を必ず含む完全なJSONだけを返してください。";
                if ($last_raw) $attempt_prompt .= "\n前回返答:\n" . mb_substr($last_raw, 0, 1800, 'UTF-8');
            }

            $raw = $this->call_gemini_raw($attempt_prompt, $attempt === 1 ? 0.35 : 0.15, 1800);
            if (is_wp_error($raw)) {
                $planner_error = $raw->get_error_message();
                continue;
            }

            $last_raw = $raw;
            $candidate = json_decode($raw, true);
            if (!is_array($candidate)) {
                $clean = preg_replace('/^```(?:json)?\\s*|\\s*```$/i', '', $raw);
                $candidate = json_decode($clean, true);
            }
            if (!is_array($candidate)) { $planner_error = 'JSON解析失敗'; continue; }

            $missing = [];
            foreach (['title','keyword','category','excerpt','seo_title'] as $k) {
                if (empty($candidate[$k])) $missing[] = $k;
            }
            if ($missing) { $planner_error = '不足: ' . implode(', ', $missing); continue; }
            if (!isset($map[$candidate['category']])) { $planner_error = 'カテゴリ不正'; continue; }

            $candidate_title = sanitize_text_field($candidate['title']);
            $duplicate = false;
            foreach ($titles as $existing_title) {
                if ($this->normalize_title_key($existing_title) === $this->normalize_title_key($candidate_title)) { $duplicate = true; break; }
            }
            if ($duplicate) { $planner_error = '既存タイトルと重複'; continue; }

            $data = $candidate;
            break;
        }

        if (!is_array($data)) {
            $fallback_title = '40代男性のスキンケア基本｜老け見えを防ぐ最低限の習慣';
            $base_title = $fallback_title;
            $n = 2;
            $existing_keys = array_map([$this, 'normalize_title_key'], $titles);
            while (in_array($this->normalize_title_key($fallback_title), $existing_keys, true)) {
                $fallback_title = $base_title . ' 実践編' . $n;
                $n++;
            }
            $data = [
                'title' => $fallback_title,
                'keyword' => '40代 男性 スキンケア 基本',
                'category' => '肌・老け見え',
                'excerpt' => '40代男性が毎日続けやすい最低限のスキンケアを、洗顔・保湿・紫外線対策の順に整理します。',
                'seo_title' => $fallback_title,
                'amazon_query' => 'メンズ オールインワン 保湿',
                'reason' => '企画JSON不備のため自動フォールバック: ' . $planner_error,
            ];
        }

        $title = sanitize_text_field($data['title']);
        $cfg = $map[$data['category']];'''

if old not in text:
    raise SystemExit('planner replacement anchor not found')
text = text.replace(old, new, 1)
php.write_text(text, encoding='utf-8')
print('planner patched to 0.18.6')