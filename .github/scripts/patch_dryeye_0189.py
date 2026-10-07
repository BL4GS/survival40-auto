from pathlib import Path

php = Path('survival40-auto/survival40-auto.php')
text = php.read_text(encoding='utf-8')

text = text.replace(' * Version: 0.18.8\n', ' * Version: 0.18.9\n', 1)
text = text.replace("    const VERSION = '0.18.8';", "    const VERSION = '0.18.9';", 1)
text = text.replace('<h1>Survival40 Auto v0.18.8</h1>', '<h1>Survival40 Auto v0.18.9</h1>', 1)

# Dedicated dry-eye evidence group.
eye_anchor = """            'eye' => [
"""
dryeye_group = r"""            'dryeye' => [
                [
                    'id' => 1,
                    'name' => 'ドライアイ研究会「ドライアイとは」',
                    'url' => 'https://dryeye.ne.jp/for-general/dryeye-summary/',
                    'notes' => [
                        'ドライアイは涙液層の安定性が低下し、眼不快感や視機能異常を生じ、眼表面の障害を伴うことがある疾患。',
                        '加齢、空調、パソコンやスマートフォンの長時間使用、コンタクトレンズ装用などが関連要因として挙げられている。',
                    ],
                ],
                [
                    'id' => 2,
                    'name' => 'ドライアイ研究会「ドライアイのケア」',
                    'url' => 'https://dryeye.ne.jp/for-general/dryeye-care/',
                    'notes' => [
                        '画面作業では、まばたきを意識し、休憩を取り、画面を目より下に置くなどの環境調整が推奨されている。',
                        'エアコンの風が直接顔に当たらないようにし、室内が乾燥する場合は加湿などを検討する。',
                        '市販点眼液や洗浄液の乱用は、防腐剤や刺激物、自分の涙を洗い流すことなどにより症状を悪化させる場合があるため、自己判断を続けず眼科で適切な指導を受けることが大切。',
                    ],
                ],
                [
                    'id' => 3,
                    'name' => 'ドライアイ研究会「ドライアイの治療方法」',
                    'url' => 'https://dryeye.ne.jp/for-general/dryeye-summary/dryeye-treatment/',
                    'notes' => [
                        'ドライアイの治療には点眼治療や涙点プラグなどがあり、症状やタイプに応じて眼科で治療法が選択される。',
                        '人工涙液、ヒアルロン酸製剤、ジクアホソル、レバミピドなどが用いられるが、処方薬の選択は医療機関で行う。',
                    ],
                ],
            ],
"""
if eye_anchor not in text:
    raise SystemExit('eye source anchor not found')
text = text.replace(eye_anchor, dryeye_group + eye_anchor, 1)

# Route dry-eye topics before the broader eye-topic branch.
old_route = """        if (preg_match('/(目|眼|視力|老視|老眼|眼精疲労|ドライアイ|アイケア|老眼鏡|眼鏡)/u', $eye_text)) {
            $cfg['source_group'] = 'eye';
            $cfg['ymyl'] = 1;
        }"""
new_route = """        if (preg_match('/(ドライアイ|目の乾燥|眼の乾燥|乾燥感)/u', $eye_text)) {
            $cfg['source_group'] = 'dryeye';
            $cfg['ymyl'] = 1;
        } elseif (preg_match('/(目|眼|視力|老視|老眼|眼精疲労|アイケア|老眼鏡|眼鏡)/u', $eye_text)) {
            $cfg['source_group'] = 'eye';
            $cfg['ymyl'] = 1;
        }"""
if old_route not in text:
    raise SystemExit('eye routing anchor not found')
text = text.replace(old_route, new_route, 1)

# Topic-specific writing guard so dry-eye articles do not drift into presbyopia or blue-light articles.
prompt_anchor = """        $source_context = $this->source_context($p['source_group'] ?? 'aga');

        return """
replacement = """        $source_context = $this->source_context($p['source_group'] ?? 'aga');

        $topic_rules = '';
        if (($p['source_group'] ?? '') === 'dryeye') {
            $topic_rules =
                "【ドライアイ記事の追加ルール】\\n"
                . "- 本文の中心はドライアイそのものにする。老眼・老眼鏡・度数選びを主題化しない。\\n"
                . "- ブルーライトカット眼鏡を主な対策として扱わない。触れる場合も『ドライアイ対策の中心ではない』と短く整理する。\\n"
                . "- 生活環境では、まばたき、休憩、画面位置、空調の直風、室内乾燥、コンタクトレンズなど、参考資料で確認できる項目を優先する。\\n"
                . "- 市販点眼薬は『効能・用法を守れば何でもよい』と書かない。市販点眼液や洗浄液の乱用で悪化する場合があること、防腐剤や刺激物への注意、症状が続く場合は眼科受診を明記する。\\n"
                . "- 処方薬（ヒアルロン酸、ジクアホソル、レバミピド等）は一般情報として紹介してもよいが、特定薬を自己判断で選ぶよう勧めない。\\n"
                . "- タイトルに『点眼薬』が含まれる場合でも、OTC商品の比較記事にせず、セルフケアの限界と受診目安を明確にする。\\n\\n";
        }

        return """
if prompt_anchor not in text:
    raise SystemExit('build_prompt anchor not found')
text = text.replace(prompt_anchor, replacement, 1)

# Inject topic rules into the prompt immediately after reader definition.
reader_anchor = """. "【読者】40代男性。美容・健康に詳しくない一般読者。\\n\\n"
        . "【この記事で使える医療・健康の参考情報】"""
reader_repl = """. "【読者】40代男性。美容・健康に詳しくない一般読者。\\n\\n"
        . $topic_rules
        . "【この記事で使える医療・健康の参考情報】"""
if reader_anchor not in text:
    raise SystemExit('prompt insertion anchor not found')
text = text.replace(reader_anchor, reader_repl, 1)

php.write_text(text, encoding='utf-8')
print('patched to 0.18.9')
