from pathlib import Path

php = Path('survival40-auto/survival40-auto.php')
text = php.read_text(encoding='utf-8')

text = text.replace(' * Version: 0.18.7\n', ' * Version: 0.18.8\n', 1)
text = text.replace("    const VERSION = '0.18.7';", "    const VERSION = '0.18.8';", 1)
text = text.replace('<h1>Survival40 Auto v0.18.7</h1>', '<h1>Survival40 Auto v0.18.8</h1>', 1)

# Eye-related plans must use eye-specific sources, not dermatology sources.
old_route = """        if (preg_match('/(目|眼|視力|老視|老眼|眼精疲労|ドライアイ|アイケア)/u', $eye_text)) {
            $cfg['source_group'] = 'skin';
            $cfg['ymyl'] = 1;
        }"""
new_route = """        if (preg_match('/(目|眼|視力|老視|老眼|眼精疲労|ドライアイ|アイケア|老眼鏡|眼鏡)/u', $eye_text)) {
            $cfg['source_group'] = 'eye';
            $cfg['ymyl'] = 1;
        }"""
if old_route not in text:
    raise SystemExit('eye route anchor not found')
text = text.replace(old_route, new_route, 1)

# Add trusted eye sources to the source library.
fn = text.find('function trusted_sources(')
if fn < 0:
    raise SystemExit('trusted_sources function not found')
arr = text.find('$all = [', fn)
if arr < 0:
    raise SystemExit('trusted_sources array not found')
insert_at = arr + len('$all = [')
eye_group = r'''
            'eye' => [
                [
                    'id' => 1,
                    'name' => '公益社団法人 日本眼科医会「40代で始まる目の老化」',
                    'url' => 'https://www.gankaikai.or.jp/health/37/',
                    'notes' => [
                        '老視では近くにピントを合わせにくくなり、用途や作業距離に合った眼鏡選びが重要。',
                        '老眼だと思っていても他の眼疾患が隠れる場合があるため、見え方の変化が気になる場合は眼科で検査を受けることが大切。',
                        '老眼鏡は生活スタイルや用途で適切な度数が異なり、合わない眼鏡は眼精疲労の原因になり得る。',
                    ],
                ],
                [
                    'id' => 2,
                    'name' => 'Cochrane「Blue-light filtering spectacle lenses」',
                    'url' => 'https://www.cochrane.org/evidence/CD013244_blue-light-filtering-spectacle-lenses-visual-performance-macular-back-part-eye-protection-and',
                    'notes' => [
                        'ブルーライトカット眼鏡は、通常レンズと比べてコンピューター作業時の短期的な眼精疲労を明確に軽減するとは示されていない。',
                        '視力への有意な利点はほとんど、または全くない可能性があり、睡眠への効果も不明確。',
                    ],
                ],
            ],
'''
text = text[:insert_at] + eye_group + text[insert_at:]

# Stronger presbyopia/reader guidance.
needle = '        . "- UV400は製品表示の一つとして扱い、万能な品質保証や効果保証として書かない。\\n"'
extra = needle + \
'        . "- 老眼鏡の記事では、年齢だけで度数を決めたり「まず+1.0から」と一律に勧めない。作業距離・左右差・乱視などで適切な度数は変わるため、見え方に不安がある場合は眼科での検査を案内する。\\n"' + \
'        . "- 老眼鏡の度数は強いほど良いものではなく、用途と見たい距離に合わせるという説明を優先する。\\n"'
if needle not in text:
    raise SystemExit('eye prompt anchor not found')
text = text.replace(needle, extra, 1)

# Flag common over-prescriptive reader advice in safety scan.
old_scan = """foreach (['必ず生える','絶対生える','必ず治る','絶対治る','AGAになる原因です','血流が悪いから抜け毛','脂っこい食事でAGA','医学的に最も多く','一番多い原因','最も多い原因','必ず改善する','絶対改善する'] as $p)"""
new_scan = """foreach (['必ず生える','絶対生える','必ず治る','絶対治る','AGAになる原因です','血流が悪いから抜け毛','脂っこい食事でAGA','医学的に最も多く','一番多い原因','最も多い原因','必ず改善する','絶対改善する','まずは弱めの度数（+1.0','一番弱い度数（+1.0'] as $p)"""
if old_scan in text:
    text = text.replace(old_scan, new_scan, 1)

php.write_text(text, encoding='utf-8')
print('patched to 0.18.8')
