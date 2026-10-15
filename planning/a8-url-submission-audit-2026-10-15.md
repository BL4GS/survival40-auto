# Survival40 A8.net 広告掲載URLの監査（2026-10-15 JST）

公式資料:
- https://a8pr.jp/2023/12/07/start-submitting-advertising-url/
- https://support.a8.net/a8/as/faq/manual/ad_url_manage.php

## 原則
- 提携中かどうかにかかわらず、**現に広告を貼っているページ**を「プログラムID × URL」で対応づけてA8に提出する。サイドバー等で全ページ共通の広告は確認可能な1ページで可（広告主個別条件が優先）。
- WordPress公開記事28本を REST API `content.rendered` で走査し、A8の `a8mat` とバナーURL `mid=s...` を照合。WordPress公開固定ページ1本にA8広告なし。**公開記事14本で広告掲載15件**が確認された（14プログラム、1プログラムが2記事に掲載され、1記事に2プログラム掲載）。
- ALGOは**所有者が2026-10-15にA8広告掲載URL提出済みと報告**。残り14行は提出未確認。オーナー用のアップロードCSVを作成したが、**A8管理画面への一括提出は未実行**。行は公式仕様どおりCSVのA列 program ID、B列実URL、ヘッダーなし、UTF-8。
- 同一記事に複数のプログラムなら、それぞれのプログラムごとに1行が必要。広告のないページは提出不要。PR表示はページ側でも必要。
- 今後新しく広告を貼る記事は公開直後の管理対象にする。GitHubトラッカーを更新しても、A8への提出が自動で行われるわけではない。

## 公開中のA8広告（A8に提出すべき15行）
| # | Program ID | 広告案件 | WP post | 掲載記事URL | A8提出状況 |
|---|---|---|---:|---|---|
| 1 | s00000021719001 | ULTORA | 450 | https://www.survival40.com/40s-male-protein-how-to-choose/ | CSV作成済み・提出待ち |
| 2 | s00000014286004 | NULL オールインワン | 438 | https://www.survival40.com/40s-male-all-in-one-skincare-guide/ | CSV作成済み・提出待ち |
| 3 | s00000007191012 | プレミアムブラックシャンプー | 442 | https://www.survival40.com/40s-male-scalp-shampoo-guide/ | CSV作成済み・提出待ち |
| 4 | s00000023792001 | DELISH KITCHEN Meals | 514 | https://www.survival40.com/40s-fatigue-food-meal-balance/ | CSV作成済み・提出待ち |
| 5 | s00000026776002 | RingConn 第2世代 | 400 | https://www.survival40.com/40s-male-waking-at-night/ | CSV作成済み・提出待ち |
| 6 | s00000016652002 | マイまくら | 387 | https://www.survival40.com/40s-fatigue-sleep-habits/ | CSV作成済み・提出待ち |
| 7 | s00000020311001 | マッスルデリ | 393 | https://www.survival40.com/40s-male-belly-activity-fitness/ | CSV作成済み・提出待ち |
| 8 | s00000013307009 | MONOVO | 533 | https://www.survival40.com/monovo-hair-tonic-grow-gel-guide/ | CSV作成済み・提出待ち |
| 9 | s00000020317006 | HOLO BELL UV | 396 | https://www.survival40.com/40s-male-dark-spots-uv-care/ | CSV作成済み・提出待ち |
| 10 | s00000016652002 | マイまくら | 433 | https://www.survival40.com/40s-male-pillow-how-to-choose/ | CSV作成済み・提出待ち |
| 11 | s00000020317010 | HOLO BELL ボディソープ | 454 | https://www.survival40.com/40s-male-body-soap-odor-guide/ | CSV作成済み・提出待ち |
| 12 | s00000021920005 | ROOT BEAUTÉ | 442 | https://www.survival40.com/40s-male-scalp-shampoo-guide/ | CSV作成済み・提出待ち |
| 13 | s00000027814001 | 薬用ナノインパクト8 | 380 | https://www.survival40.com/hair-tonic-vs-aga-treatment/ | CSV作成済み・提出待ち |
| 14 | s00000027668002 | ハグラビ | 581 | https://www.survival40.com/40s-hugravi-weighted-blanket-guide/ | CSV作成済み・提出待ち |
| 15 | s00000027668001 | ALGO Chair Pro | 585 | https://www.survival40.com/40s-algo-chair-pro-before-buy/ | 提出済み（オーナー報告） |

## 予約公開済みのA8広告（記事公開後に登録、未公開URLはまだ提出しない）
| Program ID | 公開予定 | WP ID | Slug | 対応 |
|---|---|---|---|---|
| s00000027703001 | 2026-10-19 21:00 JST | #518 | (actual published permalink needs verifying) | 公開後、A8追跡と canonical permalink を確認して提出 |
| s00000020311001 | 2026-10-21 21:00 JST | #542 | 40s-frozen-meal-delivery-cost-subscription | 公開後、A8追跡と canonical permalink を確認して提出 |
| s00000016652002 | 2026-10-22 21:00 JST | #543 | 40s-custom-pillow-vs-adjustable | 公開後、A8追跡と canonical permalink を確認して提出 |
| s00000021719001 | 2026-10-23 21:00 JST | #544 | 40s-wpc-vs-wpi-protein | 公開後、A8追跡と canonical permalink を確認して提出 |

## 提携済みでも広告未掲載（まだ提出不要）
- `s00000014723001` にんにく玉本舗 国内産にんにく玉ゴールド（本日オーナーからバナーと条件受領、掲載未実施）
- `s00000015695001` RIZAP（来店完了が成果条件、広告表現の条件確認中）
- `s00000027467001` BIOAESTECH（女性中心のターゲット。Survival40のメイン読者との相性が合う掲載記事を未選定）
- `s00000014286003` NULL ブラジリアンワックス（原稿作成済み、未公開）

## 次回実行チェック
1. CSVアップロード後にプログラムの「提出済みURL」一覧をユーザーに確認してもらう（**今は提出済みと書かない**）。
2. 新しいWordPress予約記事が公開されたらA8リンクの有無を再取得し、URL登録用CSV差分を作る。
3. 毎回、プログラム終了・リンク切れ・PR表示違反も監査対象にする。A8の会員サイトに接続されたツールがないため、実際のA8アップロードはユーザー操作が必要。
