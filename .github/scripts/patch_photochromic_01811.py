from pathlib import Path

php = Path('survival40-auto/survival40-auto.php')
text = php.read_text(encoding='utf-8')

text = text.replace(' * Version: 0.18.10\n', ' * Version: 0.18.11\n', 1)
text = text.replace("    const VERSION = '0.18.10';", "    const VERSION = '0.18.11';", 1)
text = text.replace('<h1>Survival40 Auto v0.18.10</h1>', '<h1>Survival40 Auto v0.18.11</h1>', 1)

# Add dedicated photochromic-lens sources before the general eye group.
anchor = """            'eye' => [
"""
group = r"""            'photochromic' => [
                [
                    'id' => 1,
                    'name' => 'HOYA ビジョンケアカンパニー「調光レンズ」',
                    'url' => 'https://www.vc.hoya.co.jp/products/suntech/',
                    'notes' => [
                        '調光レンズは紫外線の強さや温度などの装用環境によって発色濃度や退色速度が変わる。',
                        '一般に低温時は濃く発色しやすく、高温時は発色が抑えられる傾向がある。',
                        '紫外線カットガラスに覆われた車内では、紫外線で発色する一般的な調光レンズは濃くなりにくい。',
                        '可視光にも反応するタイプでは、紫外線がカットされた車内でも発色する製品がある。',
                        '濃い状態から淡く戻るまで時間がかかるため、トンネルや夕暮れなど急に暗くなる場面では注意が必要。',
                    ],
                ],
                [
                    'id' => 2,
                    'name' => '公益社団法人 日本眼科医会「40代で始まる目の老化」',
                    'url' => 'https://www.gankaikai.or.jp/health/37/',
                    'notes' => [
                        '40代以降は老視など見え方の変化を感じやすく、生活スタイルや用途に合った眼鏡選びが重要。',
                        '見え方に不安がある場合や眼疾患が疑われる場合は眼科での確認が大切。',
                    ],
                ],
            ],
"""
if anchor not in text:
    raise SystemExit('eye source anchor not found')
text = text.replace(anchor, group + anchor, 1)

# Route photochromic topics before broader eye routing.
old = """        if (preg_match('/(ドライアイ|目の乾燥|眼の乾燥|乾燥感)/u', $eye_text)) {
            $cfg['source_group'] = 'dryeye';
            $cfg['ymyl'] = 1;
        } elseif (preg_match('/(目|眼|視力|老視|老眼|眼精疲労|アイケア|老眼鏡|眼鏡)/u', $eye_text)) {
            $cfg['source_group'] = 'eye';
            $cfg['ymyl'] = 1;
        }"""
new = """        if (preg_match('/(調光レンズ|フォトクロミック|可視光調光)/u', $eye_text)) {
            $cfg['source_group'] = 'photochromic';
            $cfg['ymyl'] = 1;
        } elseif (preg_match('/(ドライアイ|目の乾燥|眼の乾燥|乾燥感)/u', $eye_text)) {
            $cfg['source_group'] = 'dryeye';
            $cfg['ymyl'] = 1;
        } elseif (preg_match('/(目|眼|視力|老視|老眼|眼精疲労|アイケア|老眼鏡|眼鏡)/u', $eye_text)) {
            $cfg['source_group'] = 'eye';
            $cfg['ymyl'] = 1;
        }"""
if old not in text:
    raise SystemExit('eye routing anchor not found')
text = text.replace(old, new, 1)

# Re-resolve evidence source from actual article title/keyword.
old2 = """        if (preg_match('/(ドライアイ|目の乾燥|眼の乾燥|乾燥感)/u', $article_eye_text)) {
            $resolved_source_group = 'dryeye';
        } elseif (preg_match('/(目|眼|視力|老視|老眼|眼精疲労|アイケア|老眼鏡|眼鏡|メガネ)/u', $article_eye_text)) {
            $resolved_source_group = 'eye';
        }"""
new2 = """        if (preg_match('/(調光レンズ|フォトクロミック|可視光調光)/u', $article_eye_text)) {
            $resolved_source_group = 'photochromic';
        } elseif (preg_match('/(ドライアイ|目の乾燥|眼の乾燥|乾燥感)/u', $article_eye_text)) {
            $resolved_source_group = 'dryeye';
        } elseif (preg_match('/(目|眼|視力|老視|老眼|眼精疲労|アイケア|老眼鏡|眼鏡|メガネ)/u', $article_eye_text)) {
            $resolved_source_group = 'eye';
        }"""
if old2 not in text:
    raise SystemExit('resolved source anchor not found')
text = text.replace(old2, new2, 1)

# Topic-specific editorial rules.
topic_anchor = """        if ($resolved_source_group === 'dryeye') {
"""
if topic_anchor not in text:
    raise SystemExit('topic rules anchor not found')

insert_rules = r"""        if ($resolved_source_group === 'photochromic') {
            $topic_rules =
                "【調光レンズ記事の追加ルール】\n"
                . "- 記事の中心は調光レンズの発色特性、温度依存、車内での挙動、退色時間、用途適合にする。\n"
                . "- 『紫外線量だけで色が変わる』と一般化しない。紫外線で発色するタイプと、可視光にも反応するタイプがあることを区別する。\n"
                . "- 一般的な紫外線反応型はUVカットガラスの車内では濃くなりにくいが、可視光反応型は車内でも発色する製品があることを明記する。\n"
                . "- 高温では発色が抑えられ、低温では濃くなりやすく退色が遅くなる傾向を、製品特性として説明する。\n"
                . "- トンネル、屋内駐車場、夕暮れなど急に暗くなる場面では、濃色から淡色へ戻るまで時間がかかる点を安全上の注意として扱う。\n"
                . "- ブルーライトの話は主題ではない。製品に当該機能がある場合の補足に限定し、本文の大きな節にしない。\n"
                . "- 『屋外から室内に戻ったときに急なまぶしさ』など、調光レンズの特性と直接関係しない症状を導入の根拠にしない。\n"
                . "- 調光特性についてはHOYA等のレンズメーカー一次情報を参考情報に必ず含める。\n\n";
        } elseif ($resolved_source_group === 'dryeye') {
"""
text = text.replace(topic_anchor, insert_rules, 1)

php.write_text(text, encoding='utf-8')
print('patched to 0.18.11')
