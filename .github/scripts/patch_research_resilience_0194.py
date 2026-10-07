from pathlib import Path
p=Path("survival40-auto/survival40-auto.php")
s=p.read_text(encoding="utf-8")
s=s.replace(" * Version: 0.19.3\n"," * Version: 0.19.4\n",1)
s=s.replace("    const VERSION = '0.19.3';","    const VERSION = '0.19.4';",1)
s=s.replace("<h1>Survival40 Auto v0.19.3</h1>","<h1>Survival40 Auto v0.19.4</h1>",1)

old="""        if (is_wp_error($res) || wp_remote_retrieve_response_code($res) < 200 || wp_remote_retrieve_response_code($res) >= 300) {
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

        $raw = trim($raw);"""
new="""        $grounded_sources = [];
        if (is_wp_error($res) || wp_remote_retrieve_response_code($res) < 200 || wp_remote_retrieve_response_code($res) >= 300) {
            $raw = $this->call_gemini_raw($prompt, 0.1, 2400);
            if (is_wp_error($raw)) return $raw;
        } else {
            $data = json_decode(wp_remote_retrieve_body($res), true);

            $chunks = $data['candidates'][0]['groundingMetadata']['groundingChunks'] ?? [];
            foreach ($chunks as $chunk) {
                $web = $chunk['web'] ?? [];
                $u = esc_url_raw($web['uri'] ?? '');
                $t = sanitize_text_field($web['title'] ?? '');
                if (!$u || !$t) continue;
                $grounded_sources[] = [
                    'name' => $t,
                    'url' => $u,
                    'why' => 'Google Search groundingで取得したテーマ関連資料',
                    'source_type' => 'other',
                ];
                if (count($grounded_sources) >= 5) break;
            }

            if (count($grounded_sources) >= 2) {
                return ['sources' => $grounded_sources];
            }

            $raw = $data['candidates'][0]['content']['parts'][0]['text'] ?? '';
            if (!$raw) {
                $raw = $this->call_gemini_raw($prompt, 0.1, 2400);
                if (is_wp_error($raw)) return $raw;
            }
        }

        $raw = trim($raw);"""
if old not in s: raise SystemExit("discover anchor not found")
s=s.replace(old,new,1)

old2="""        if (!$accepted) return new WP_Error('research_empty', '記事テーマを裏付ける資料を取得できませんでした。');"""
new2="""        if (!$accepted) {
            // Do not kill the whole automation cycle. Keep the article as a draft and let the reviewer
            // explain that research failed. This prevents one difficult topic from stopping automation.
            return [
                'mode' => 'research_failed',
                'sources' => [],
                'context' => "【調査結果】外部資料を取得できませんでした。この記事は公開不可として下書き保存し、本文では断定を避けてください。",
            ];
        }"""
if old2 not in s: raise SystemExit("empty anchor not found")
s=s.replace(old2,new2,1)

p.write_text(s,encoding="utf-8")
print("patched to 0.19.4")
