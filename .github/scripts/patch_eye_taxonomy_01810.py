from pathlib import Path

php = Path('survival40-auto/survival40-auto.php')
text = php.read_text(encoding='utf-8')

text = text.replace(' * Version: 0.18.9\n', ' * Version: 0.18.10\n', 1)
text = text.replace("    const VERSION = '0.18.9';", "    const VERSION = '0.18.10';", 1)
text = text.replace('<h1>Survival40 Auto v0.18.9</h1>', '<h1>Survival40 Auto v0.18.10</h1>', 1)

# Planner taxonomy rule: eye topics belong to 40代の不調, not fatigue/sleep.
needle = '            . "ブルーライトカット眼鏡を『目の疲れ対策』『目を守る』という効能前提の企画にしない。扱う場合はエビデンスを確認する記事、またはUV対策・フィット感など別論点と明確に分ける。\\n\\n"'
insert = '            . "ブルーライトカット眼鏡を『目の疲れ対策』『目を守る』という効能前提の企画にしない。扱う場合はエビデンスを確認する記事、またはUV対策・フィット感など別論点と明確に分ける。\\n"' + \
'            . "目・眼・老眼・老眼鏡・眼鏡・ドライアイ・視力・眼精疲労を主題にする記事は category を必ず「40代の不調」にする。「疲労・睡眠」には入れない。\\n\\n"'
if needle not in text:
    raise SystemExit('planner eye taxonomy anchor not found')
text = text.replace(needle, insert, 1)

# Force category before resolving category config. This also fixes related-article routing.
old = """        $cfg = $map[$data['category']];
        $eye_text = $title . ' ' . sanitize_text_field($data['keyword']);
        if (preg_match('/(ドライアイ|目の乾燥|眼の乾燥|乾燥感)/u', $eye_text)) {
            $cfg['source_group'] = 'dryeye';
            $cfg['ymyl'] = 1;
        } elseif (preg_match('/(目|眼|視力|老視|老眼|眼精疲労|アイケア|老眼鏡|眼鏡)/u', $eye_text)) {
            $cfg['source_group'] = 'eye';
            $cfg['ymyl'] = 1;
        }"""
new = """        $eye_text = $title . ' ' . sanitize_text_field($data['keyword']);
        if (preg_match('/(ドライアイ|目の乾燥|眼の乾燥|乾燥感|目|眼|視力|老視|老眼|眼精疲労|アイケア|老眼鏡|眼鏡)/u', $eye_text)) {
            if (isset($map['40代の不調'])) {
                $data['category'] = '40代の不調';
            }
        }

        $cfg = $map[$data['category']];
        if (preg_match('/(ドライアイ|目の乾燥|眼の乾燥|乾燥感)/u', $eye_text)) {
            $cfg['source_group'] = 'dryeye';
            $cfg['ymyl'] = 1;
        } elseif (preg_match('/(目|眼|視力|老視|老眼|眼精疲労|アイケア|老眼鏡|眼鏡)/u', $eye_text)) {
            $cfg['source_group'] = 'eye';
            $cfg['ymyl'] = 1;
        }"""
if old not in text:
    raise SystemExit('eye routing/category anchor not found')
text = text.replace(old, new, 1)

# Defense in depth: choose evidence source again from the actual article title/keyword.
old2 = """        $source_context = $this->source_context($p['source_group'] ?? 'aga');

        $topic_rules = '';"""
new2 = """        $resolved_source_group = $p['source_group'] ?? 'aga';
        $article_eye_text = sanitize_text_field(($p['title'] ?? '') . ' ' . ($p['keyword'] ?? ''));
        if (preg_match('/(ドライアイ|目の乾燥|眼の乾燥|乾燥感)/u', $article_eye_text)) {
            $resolved_source_group = 'dryeye';
        } elseif (preg_match('/(目|眼|視力|老視|老眼|眼精疲労|アイケア|老眼鏡|眼鏡|メガネ)/u', $article_eye_text)) {
            $resolved_source_group = 'eye';
        }
        $source_context = $this->source_context($resolved_source_group);

        $topic_rules = '';"""
if old2 not in text:
    raise SystemExit('source context anchor not found')
text = text.replace(old2, new2, 1)

# Keep topic rules aligned with the resolved source group.
old3 = """        if (($p['source_group'] ?? '') === 'dryeye') {"""
new3 = """        if ($resolved_source_group === 'dryeye') {"""
if old3 not in text:
    raise SystemExit('dryeye rule anchor not found')
text = text.replace(old3, new3, 1)

# Eye article relevance rules.
topic_anchor = """        if ($resolved_source_group === 'dryeye') {
            $topic_rules ="""
if topic_anchor not in text:
    raise SystemExit('topic rules anchor not found')

# Insert general eye rules after the dry-eye block by locating its terminating marker.
marker = """        }

        return """
idx = text.find(marker, text.find(topic_anchor))
if idx < 0:
    raise SystemExit('topic rules end anchor not found')
eye_rules = r'''        } elseif ($resolved_source_group === 'eye') {
            $topic_rules =
                "【眼科・眼鏡記事の追加ルール】\n"
                . "- 老眼鏡・デスクワーク用眼鏡では、年齢だけで度数を決めず、作業距離・左右差・乱視・用途を確認する。\n"
                . "- 中近・遠近・単焦点などの説明は一般論に留め、個人に最適な設計を断定しない。\n"
                . "- ブルーライトカットを眼精疲労改善の主対策として売らない。比較試験で明確な優位性が示されていないことを必要に応じて説明する。\n"
                . "- UV対策とブルーライト対策を分ける。\n"
                . "- 見え方の変化、痛み、急なかすみ等がある場合は眼科受診を案内する。\n"
                . "- 記事の参考情報は眼科・眼鏡領域の資料だけを使い、睡眠・皮膚など別分野の資料を流用しない。\n\n";
        }

'''
text = text[:idx] + eye_rules + text[idx+len("        }\n"):]

php.write_text(text, encoding='utf-8')
print('patched to 0.18.10')
