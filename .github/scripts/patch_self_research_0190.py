from pathlib import Path
import re

php = Path("survival40-auto/survival40-auto.php")
text = php.read_text(encoding="utf-8")

text = text.replace(" * Version: 0.18.11\n", " * Version: 0.19.0\n", 1)
text = text.replace("    const VERSION = '0.18.11';", "    const VERSION = '0.19.0';", 1)
text = text.replace("<h1>Survival40 Auto v0.18.11</h1>", "<h1>Survival40 Auto v0.19.0</h1>", 1)

# Dynamic research evidence overrides fixed topic tables when available.
old_ctx = "$source_context = $this->source_context($resolved_source_group);"
new_ctx = "$source_context = !empty($p['_research_context']) ? $p['_research_context'] : $this->source_context($resolved_source_group);"
if old_ctx not in text:
    raise SystemExit("build_prompt source context anchor not found")
text = text.replace(old_ctx, new_ctx, 1)

pattern = re.compile(
    r"    private function generate_planned_article\(\$p\) \{.*?\n    \}\n\n    public function handle_run_auto_once\(\) \{",
    re.S
)
m = pattern.search(text)
if not m:
    raise SystemExit("generate_planned_article block not found")

replacement = r'''    private function research_discover_sources($p, $failed_urls = []) {
        $s = $this->settings();
        if (empty($s['gemini_api_key'])) return new WP_Error('no_key', 'Gemini API Keyが未設定です。');

        $failed = $failed_urls ? ("\n取得失敗URL:\n- " . implode("\n- ", array_slice($failed_urls, 0, 8))) : '';
        $prompt =
            "あなたはSurvival40のリサーチャーです。\n"
            . "記事を書く前に、記事テーマを直接裏付ける信頼できる資料を探してください。\n"
            . "タイトル: {$p['title']}\nキーワード: {$p['keyword']}\nカテゴリ: {$p['category']}\n\n"
            . "優先: 日本の省庁・公的機関・専門学会・大学・公的研究機関。製品仕様はメーカー公式一次情報。医学的主張は診療ガイドラインや系統的レビュー。\n"
            . "禁止: アフィリエイトサイト、まとめ、個人ブログ、検索結果URL、記事と関係の薄い資料の数合わせ。\n"
            . "主要論点を直接支える個別ページURLを2〜5件返すこと。\n"
            . $failed
            . "\nJSONだけ返すこと。形式: "
            . "{\"sources\":[{\"name\":\"資料名\",\"url\":\"https://...\",\"why\":\"支える論点\",\"source_type\":\"government|society|university|systematic_review|manufacturer|other\"}]}";

        $model = $s['model'] ?: 'gemini-3.5-flash-lite';
        $url = 'https://generativelanguage.googleapis.com/v1beta/models/' . rawurlencode($model) . ':generateContent';
        $body = [
            'contents' => [[ 'role' => 'user', 'parts' => [['text' => $prompt]] ]],
            'tools' => [[ 'google_search' => (object)[] ]],
            'generationConfig' => ['temperature' => 0.1, 'maxOutputTokens' => 2400],
        ];

        $res = wp_remote_post($url, [
            'headers' => ['Content-Type' => 'application/json', 'x-goog-api-key' => $s['gemini_api_key']],
            'body' => wp_json_encode($body),
            'timeout' => 120,
        ]);

        if (is_wp_error($res) || wp_remote_retrieve_response_code($res) < 200 || wp_remote_retrieve_response_code($res) >= 300) {
            $raw = $this->call_gemini_raw($prompt, 0.1, 2400);
            if (is_wp_error($raw)) return $raw;
        } else {
            $data = json_decode(wp_remote_retrieve_body($res), true);
            $raw = $data['candidates'][0]['content']['parts'][0]['text'] ?? '';
            if (!$raw) {
                $raw = $this->call_gemini_raw($prompt, 0.1, 2400);
                if (is_wp_error($raw)) return $raw;
            }
        }

        $raw = trim($raw);
        if (substr($raw, 0, 1) !== '{') {
            $start = strpos($raw, '{');
            $end = strrpos($raw, '}');
            if ($start !== false && $end !== false && $end > $start) $raw = substr($raw, $start, $end - $start + 1);
        }
        $data = json_decode($raw, true);
        if (!is_array($data) || empty($data['sources']) || !is_array($data['sources'])) {
            return new WP_Error('research_json', '調査候補の解析に失敗しました。');
        }
        return $data;
    }

    private function research_fetch_source($source) {
        $url = isset($source['url']) ? esc_url_raw($source['url']) : '';
        if (!$url || !wp_http_validate_url($url) || !preg_match('#^https?://#i', $url)) return false;

        $res = wp_safe_remote_get($url, [
            'timeout' => 18,
            'redirection' => 4,
            'user-agent' => 'Survival40-Auto/' . self::VERSION,
            'headers' => ['Accept' => 'text/html,text/plain'],
        ]);
        if (is_wp_error($res)) return false;
        $code = wp_remote_retrieve_response_code($res);
        if ($code < 200 || $code >= 300) return false;

        $body = wp_remote_retrieve_body($res);
        if (!$body || strlen($body) < 300) return false;
        $body = preg_replace('#<(script|style|noscript|svg|iframe|nav|footer|form)[^>]*>.*?</\1>#is', ' ', $body);
        $plain = html_entity_decode(wp_strip_all_tags($body), ENT_QUOTES | ENT_HTML5, 'UTF-8');
        $plain = trim(preg_replace('/\s+/u', ' ', $plain));
        if (mb_strlen($plain, 'UTF-8') < 250) return false;

        return [
            'name' => sanitize_text_field($source['name'] ?? $url),
            'url' => $url,
            'why' => sanitize_text_field($source['why'] ?? ''),
            'source_type' => sanitize_key($source['source_type'] ?? 'other'),
            'text' => mb_substr($plain, 0, 6000, 'UTF-8'),
        ];
    }

    private function research_topic($p) {
        $accepted = [];
        $failed = [];

        for ($attempt = 1; $attempt <= 2 && count($accepted) < 2; $attempt++) {
            $discovery = $this->research_discover_sources($p, $failed);
            if (is_wp_error($discovery)) continue;

            foreach ($discovery['sources'] as $source) {
                if (count($accepted) >= 4) break;
                $url = isset($source['url']) ? esc_url_raw($source['url']) : '';
                if (!$url) continue;

                $duplicate = false;
                foreach ($accepted as $a) if ($a['url'] === $url) $duplicate = true;
                if ($duplicate) continue;

                $fetched = $this->research_fetch_source($source);
                if ($fetched) $accepted[] = $fetched;
                else $failed[] = $url;
            }
        }

        $mode = count($accepted) >= 2 ? 'dynamic' : 'fallback';
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
        if (!$accepted) return new WP_Error('research_empty', '記事テーマを裏付ける資料を取得できませんでした。');

        $lines = [];
        foreach ($accepted as $i => $src) {
            $n = $i + 1;
            $lines[] = "【調査資料{$n}】{$src['name']}";
            $lines[] = "URL: {$src['url']}";
            if (!empty($src['why'])) $lines[] = "役割: {$src['why']}";
            $lines[] = "取得本文: {$src['text']}";
            $lines[] = "";
        }
        return ['mode' => $mode, 'sources' => $accepted, 'context' => implode("\n", $lines)];
    }

    private function dynamic_source_block($research) {
        $s = $this->settings();
        if (empty($s['show_sources']) || empty($research['sources'])) return '';
        $links = [];
        foreach ($research['sources'] as $src) {
            if (empty($src['url']) || empty($src['name'])) continue;
            $links[] = '<a href="' . esc_url($src['url']) . '" target="_blank" rel="noopener" style="font-size:13px !important;line-height:1.55 !important;font-weight:400 !important;text-decoration:underline !important;display:inline !important;">' . esc_html($src['name']) . '</a>';
        }
        if (!$links) return '';
        return '<div class="s40-sources" style="margin-top:32px !important;padding-top:12px !important;border-top:1px solid #ddd !important;font-size:13px !important;line-height:1.55 !important;color:#666 !important;">'
            . '<div style="font-size:12px !important;font-weight:600 !important;margin:0 0 6px !important;">参考情報</div>'
            . '<div style="font-size:13px !important;line-height:1.55 !important;margin:0 0 6px !important;">' . implode('<br>', $links) . '</div>'
            . '<div style="font-size:11px !important;line-height:1.5 !important;margin:0 !important;color:#777 !important;">※健康・医療に関わる内容は、必要に応じて専門家へご相談ください。</div>'
            . '</div>';
    }

    private function review_generated_article($p, $html, $research) {
        $prompt =
            "あなたはSurvival40の編集長兼ファクトチェッカーです。\n"
            . "タイトル: {$p['title']}\nカテゴリ: {$p['category']}\n\n"
            . "【取得済み根拠資料】\n{$research['context']}\n\n"
            . "【記事本文】\n" . wp_strip_all_tags($html) . "\n\n"
            . "主題一致、重要事実の裏付け、資料との整合、根拠のない数値・断定・効能、購入誘導による誇張を判定してください。\n"
            . "JSONだけ返すこと。形式: "
            . "{\"verdict\":\"pass|revise\",\"score\":0,\"issues\":[\"問題\"],\"unsupported_claims\":[\"根拠不足\"],\"topic_drift\":false,\"source_mismatch\":false}";

        $raw = $this->call_gemini_raw($prompt, 0.05, 2400);
        if (is_wp_error($raw)) return ['verdict'=>'revise','score'=>0,'issues'=>[$raw->get_error_message()],'unsupported_claims'=>[]];

        $raw = trim($raw);
        if (substr($raw, 0, 1) !== '{') {
            $start = strpos($raw, '{'); $end = strrpos($raw, '}');
            if ($start !== false && $end !== false && $end > $start) $raw = substr($raw, $start, $end - $start + 1);
        }
        $data = json_decode($raw, true);
        if (!is_array($data)) return ['verdict'=>'revise','score'=>0,'issues'=>['編集長レビュー解析失敗'],'unsupported_claims'=>[]];

        $score = max(0, min(100, intval($data['score'] ?? 0)));
        $data['score'] = $score;
        $data['verdict'] = (($data['verdict'] ?? '') === 'pass' && $score >= 80 && empty($data['source_mismatch'])) ? 'pass' : 'revise';
        return $data;
    }

    private function rewrite_from_review($p, $html, $research, $review) {
        $issues = implode("\n- ", array_merge($review['issues'] ?? [], $review['unsupported_claims'] ?? []));
        $prompt =
            "以下の記事を編集長レビューに従って全文修正してください。\n"
            . "取得済み資料で裏付けられる範囲だけで書き、新しい事実を勝手に追加しない。主題から外れた節は削る。\n"
            . "広告マーカーがある場合は維持。h1は使わずh2/h3。出力は本文HTMLだけ。\n\n"
            . "タイトル: {$p['title']}\nレビュー:\n- {$issues}\n\n"
            . "資料:\n{$research['context']}\n\n現在の記事:\n{$html}";
        return $this->call_gemini($prompt);
    }

    private function generate_planned_article($p) {
        $existing = get_page_by_title($p['title'], OBJECT, 'post');
        if ($existing && $existing->post_status !== 'trash') return new WP_Error('already_exists', '同名記事が既に存在します。');

        $research = $this->research_topic($p);
        if (is_wp_error($research)) return $research;

        $p['_research_context'] = $research['context'];
        $html = $this->call_gemini($this->build_prompt($p));
        if (is_wp_error($html)) return $html;

        $review = $this->review_generated_article($p, $html, $research);
        if (($review['verdict'] ?? 'revise') !== 'pass') {
            $rewritten = $this->rewrite_from_review($p, $html, $research, $review);
            if (!is_wp_error($rewritten)) {
                $html = $rewritten;
                $review = $this->review_generated_article($p, $html, $research);
            }
        }

        $warnings = $this->safety_scan($html);
        $html = $this->inject_affiliate($html, $p);
        $html .= "\n" . $this->dynamic_source_block($research);
        $html = $this->append_auto_related_links($html, $p['category']);

        $s = $this->settings();
        $status = 'draft';
        $research_ok = (($research['mode'] ?? '') === 'dynamic' && count($research['sources'] ?? []) >= 2);
        $review_ok = (($review['verdict'] ?? '') === 'pass' && intval($review['score'] ?? 0) >= 80);
        if (empty($p['ymyl']) && empty($warnings) && $research_ok && $review_ok && !empty($s['auto_publish_general'])) $status = 'publish';

        $cat = $this->category_id($p['category']);
        $source_meta = [];
        foreach ($research['sources'] ?? [] as $src) {
            $source_meta[] = ['name'=>$src['name'] ?? '', 'url'=>$src['url'] ?? '', 'source_type'=>$src['source_type'] ?? ''];
        }

        $postarr = [
            'post_title'=>$p['title'], 'post_name'=>sanitize_title($p['slug']), 'post_content'=>wp_kses_post($html),
            'post_excerpt'=>$p['excerpt'], 'post_status'=>$status, 'post_type'=>'post', 'post_category'=>$cat ? [$cat] : [],
            'meta_input'=>[
                '_survival40_keyword'=>$p['keyword'],
                '_survival40_generated'=>current_time('mysql'),
                '_survival40_ai_provider'=>'gemini',
                '_survival40_ai_model'=>$s['model'],
                '_survival40_safety_warnings'=>implode(' / ', $warnings),
                '_survival40_seo_title'=>$p['seo_title'],
                '_survival40_meta_description'=>$p['excerpt'],
                '_survival40_amazon_candidate'=>$p['amazon_candidate'] ?? '',
                '_survival40_auto_planned'=>'1',
                '_survival40_auto_reason'=>$p['planner_reason'] ?? '',
                '_survival40_ymyl'=>!empty($p['ymyl']) ? '1' : '0',
                '_survival40_research_mode'=>$research['mode'] ?? '',
                '_survival40_research_sources'=>wp_json_encode($source_meta, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
                '_survival40_review_verdict'=>$review['verdict'] ?? 'revise',
                '_survival40_review_score'=>intval($review['score'] ?? 0),
                '_survival40_review_issues'=>implode(' / ', $review['issues'] ?? []),
            ],
        ];

        $post_id = wp_insert_post($postarr, true);
        if (is_wp_error($post_id)) return $post_id;
        $this->sync_aioseo_rest($post_id, $p);

        return [
            'post_id'=>intval($post_id), 'title'=>$p['title'], 'status'=>$status, 'warnings'=>$warnings,
            'research_mode'=>$research['mode'] ?? '', 'research_sources'=>count($research['sources'] ?? []),
            'review_verdict'=>$review['verdict'] ?? 'revise', 'review_score'=>intval($review['score'] ?? 0),
        ];
    }

    public function handle_run_auto_once() {'''

text = text[:m.start()] + replacement + text[m.end():]

old_msg = "$msg = '自動生成完了: ' . $result['title'] . '（' . $result['status'] . '）';"
new_msg = "$msg = '自動生成完了: ' . $result['title'] . '（' . $result['status'] . '） / 調査' . intval($result['research_sources'] ?? 0) . '件 / レビュー' . intval($result['review_score'] ?? 0) . '点';"
if old_msg in text:
    text = text.replace(old_msg, new_msg, 1)

php.write_text(text, encoding="utf-8")
print("patched to 0.19.0")
