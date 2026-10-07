from pathlib import Path
import re

p=Path("survival40-auto/survival40-auto.php")
s=p.read_text(encoding="utf-8")
target="0.19.7"

# Version surfaces: tolerate whichever previous patch version is present.
s,n1=re.subn(r"(?m)^(\s*\*\s*Version:\s*)\d+\.\d+\.\d+\s*$",lambda m:m.group(1)+target,s,count=1)
s,n2=re.subn(r"(?m)^(\s*const\s+VERSION\s*=\s*')[^']+(';\s*)$",lambda m:m.group(1)+target+m.group(2),s,count=1)
s,n3=re.subn(r"<h1>Survival40 Auto v\d+\.\d+\.\d+</h1>","<h1>Survival40 Auto v"+target+"</h1>",s,count=1)
if not (n1 and n2 and n3):
    raise SystemExit("version surfaces not found")

# Strengthen the editor/fact-checker. This is deliberately anchored to the
# existing 0.19.1 review rule, avoiding brittle research-method rewrites.
needle = (
'            . "記事内で扱う主要論点ごとに、取得済み資料のどれが直接支えているか確認してください。'
'資料にない重要主張が1つでもあればpassにしないでください。\\n"'
)
extra = needle + (
'\n            . "資料の権威性より記事テーマとの直接関連性を優先してください。'
'公的機関・大学等でも、記事の主要論点を直接説明していない資料は根拠として数えないでください。\\n"'
'\n            . "取得資料のうち、記事タイトルの主要論点を直接裏付ける資料が2件未満なら'
'scoreは79以下、verdictはreviseにしてください。\\n"'
'\n            . "タイトルの主題から外れる節や、必要性の薄い医療・診断・別商品の選び方への脱線があれば'
'issuesに入れ、passにしないでください。\\n"'
'\n            . "「40代だから○○が増える・変化する」など年齢を理由にした主張は、'
'取得資料で直接裏付けられない限りissuesに入れてください。\\n"'
)
if needle in s and "資料の権威性より記事テーマとの直接関連性" not in s:
    s=s.replace(needle,extra,1)

# Add topic_drift to the hard pass condition when the current expression exists.
old="(($data['verdict'] ?? '') === 'pass' && $score >= 80 && empty($data['source_mismatch'])) ? 'pass' : 'revise'"
new="(($data['verdict'] ?? '') === 'pass' && $score >= 80 && empty($data['source_mismatch']) && empty($data['topic_drift'])) ? 'pass' : 'revise'"
if old in s:
    s=s.replace(old,new)

# Teach the JSON contract about topic drift if possible, without making build brittle.
if '"source_mismatch":false' in s and '"topic_drift":false' not in s:
    s=s.replace('"source_mismatch":false','"source_mismatch":false,"topic_drift":false',1)

p.write_text(s,encoding="utf-8")
print("patched to 0.19.7")
