# 2026-10-27 朝：歯ぐきの出血という検索意図の検証（編集提案・非公開）

Status: **RESEARCH ONLY / NO WORDPRESS WRITE**. This is a candidate for an evidence-led refresh, not proof of search volume or authorization to publish. Follows `PROJECT_VISION.md` and `docs/organic-distribution-rollout-2026-10-21.md`.

## 読者の困りごとと検索意図

- 主対象：40代男性を含む成人。「歯磨きで歯ぐきから血が出る」「痛くないのに出血する」「出血した場所は磨かないほうがいい？」「いつ歯科に行く？」。
- 情報要求：病名の自己診断より先に、出血を放置してよいか、当日のケア、歯科受診の判断を知りたい。歯周病と断定せず、歯磨きの力やその他の原因にも言及する。
- 年代固有の医学的断定はしない。仕事の合間に受診を迷う読者の行動判断と費用・時間の障壁を意識するが、根拠のない料金や治療期間を記さない。

## 一次情報と記述上の境界

1. 厚生労働省 e-ヘルスネット「歯周疾患の自覚症状とセルフチェック」：歯磨き時の出血・口臭・腫れ・動揺を歯周疾患のサインとして紹介し、気になる症状は歯科検査を勧める。https://kennet.mhlw.go.jp/information/information/teeth/h-03-003
2. 日本歯周病学会「歯周病の症状」：歯肉の炎症で出血しやすくなる一方、出血しないことは無病の証拠ではない。歯磨き時の出血に気づいたら早めの歯科受診を勧める。https://www.perio.jp/qa/symptom/
3. 日本口腔外科学会「歯周病だろうか？」：出血・腫れ・膿・噛みにくさ等では歯科受診を勧める。https://www.jsoms.or.jp/public/soudan/ha/shisyubyo/
4. 厚生労働省「令和6年歯科疾患実態調査」：2024年実施の全国調査。口腔の問題の社会的背景の根拠に使えるが、検索ボリュームや40代男性の個別症状の発生率と混同しない。https://www.mhlw.go.jp/stf/newpage_59190.html
5. 厚生労働省 e-ヘルスネット「歯周疾患の有病状況」：『国民の8割が歯周病』という定型的な煽りを避けるべき理由を説明。https://kennet.mhlw.go.jp/information/information/teeth/h-03-004.html

編集禁止事項：出血＝歯周病の確定診断、自己治療の保証、受診不要とする一律の日数、根拠のない「40代男性の◯割」、全身疾患との因果関係の誇張、架空の体験談、歯科の代替としてのマウスウォッシュ広告。

## 競合SERPの観察（2026-10-27、検索結果の例・順位確定ではない）

- 「歯茎から血が出る 歯磨き 出血 歯周病 原因 対処 歯科」等で歯科医療機関の解説が多数見つかった。例：
  - 武蔵小金井ハーヴェスト歯科（2026-10-24）：原因、症状別判断、受診目安。https://m-harvest-dc.com/column/1471.html
  - 荻窪ツイン歯科（2026-05-22）：セルフケア、検査・治療の流れ。https://www.ogikubo-dc.com/news/3104/
  - すずき歯科（2026-10-01）：出血と歯科で調べること。https://sdcokazaki.jp/bleeding-gums/
- 医療機関の監修・診療経験を持たない媒体が、一般的な病気解説だけで新規記事を作る優位性は弱い。読者の「出血を見た直後の次の行動」に絞り、一次情報へ誘導する方が安全。
- **検索ボリューム、検索順位、CTR、成約需要は未確認。** SERPの存在は需要の実測ではない。GSC Wizardは subscription_required で取得できなかった。

## WordPress重複照合（認証付き投稿検索、2026-10-27 JST）

- 公開 ID **389** `40s-male-bad-breath-care`：口臭の原因・対策。https://www.survival40.com/40s-male-bad-breath-care/
- 公開 ID **446** `40s-male-mouthwash-guide`：マウスウォッシュの選び方。https://www.survival40.com/40s-male-mouthwash-guide/
- 公開 ID **421** `40s-male-electric-toothbrush-guide`：電動歯ブラシの選び方。https://www.survival40.com/40s-male-electric-toothbrush-guide/
- 投稿タイトル／抜粋の検索では「歯茎」に完全一致する記事は見つからなかった。ただし検索は全文・すべての非公開投稿を網羅したことを保証しない。ID389/446等の本文取得・既存内部リンクの完全照合は今回失敗したため、**重複なしとは確定しない**。

## 次に許される一工程（ゲート付き）

1. まずID389の**現在の本文・既存リンク・編集履歴**を読み取り、歯肉出血に関する十分な説明が既にないか確認する。既存記事に短い「歯磨きで出血するなら」節を加える余地があれば、上記一次情報に基づき、早めの歯科相談を促す。本文未確認のまま追加しない。
2. ID389からID421/446へのリンクが本当に読者の次の疑問に合い、重複していなければ検討。ただし出血への対処として商品を押し売りしない。必要なら無広告とする。
3. 別記事の新規作成は、GSC実測・検索意図の差・既存記事の不足・独自の価値を検証できた場合のみ。新記事のタイトル案は「歯磨きで歯ぐきから血が出た。40代で確認したいこと」だが、**公開予定・予約・スラッグ確定ではない**。
4. 更新を実施する場合は投稿ID・ステータス・スラッグを再照合し、1記事1箇所の小変更と差分確認を行う。広告・カテゴリー・予約枠・SNS連携を変えない。
5. Discoverは適切な幅1200px以上の元画像、`max-image-preview:large`、`og:image`、画像URL取得を公開HTMLで確認してから判断。今回の直接公開ページ取得は失敗し、GitHub public-site-audit Action の成功だけでは画像適合性やDiscover流入を証明できない。

## 今回の安全境界

- WordPress/ConoHa/DB/テーマ/プラグイン/広告/SNS/予約投稿への書き込みなし。
- 2026-10-27時点で両WordPressの表示PHPは **8.4.26**（認証付き site_info）。ConoHa WINGは2026-10-22終報で8.4.26を含む提供PHP全系列への修正バックポート完了・所有者のPHP変更不要と発表。個別サーバーのパッチバイナリは直接検証していない。https://www.conoha.jp/wing/news/?ap=2015054909
- PHP公式のCVE-2026-109618 / CVE-2026-109619修正版は8.4系 **8.4.27**。ホストのバックポート適用と表示番号は区別する。https://www.php.net/archive/2026.php
- 追加のCVE-2026-115560は `session.serialize_handler` を特殊に切り替えるアプリ条件等が必要とPHP公式が案内。両サイトの該当性は未確認。設定は変更しない。https://www.php.net/archive/2026.php
- GitHub main は `bdbed00fde456c267e34c80f06af64bea84fc702`、Threads無下書き時のfail-closed修正はdraft PR #123にあり未統合。https://github.com/BL4GS/survival40-auto/pull/123
- GitHubの読み取り専用 public-site-audit run 40389569004 は成功。これは記事品質・OG画像・Discover掲載・Pinterest実公開ピンの検証完了を意味しない。https://github.com/BL4GS/survival40-auto/actions/runs/40389569004
