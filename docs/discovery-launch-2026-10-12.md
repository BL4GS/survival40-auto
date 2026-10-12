# Survival40 公開23記事を活かす集客初動 — 2026-10-12

## 方針
「自動記事量産を待つ」のではなく、**現在公開されている23記事への検索・サイト内回遊・SNS導線を先に整える**。読者に役立つ構造を優先し、広告がなくても成立する。検索順位・アクセス増を保証する施策ではない。

## 本番で確認できた現状
- WordPress公開記事 **23件**、下書き **16件**、予約 **0件**。正規ホストは `https://www.survival40.com`。
- サイト公開設定 `blog_public=1`、AIOSEOサイトマップON、robots.txtは一般の記事クロール禁止を含まない。
- robots.txt公開設定に `https://www.survival40.com/sitemap.xml` が記載されている。
- ホームページは固定ページID471。公開されたトップページの`<main>`には**少なくとも14本**の自サイト記事へのリンクを確認。残り9件の全サイト内導線・孤立性までは未確定。
- 公開23件は7カテゴリに分散（肌4、髪4、ニオイ4、口/歯4、疲労/睡眠3、体型/筋力4）。「食事・栄養」「40代の不調」は**公開0件**で、現時点のサイトの分類として将来向け。
- AIOSEO `aioseo-audit/site-get` は `sitemap_enabled=true`, `search_console_connected=false`。**これはGoogleがサイトを認識/非認識かの判定ではない**。Google Search Consoleのプロパティ確認は別途必要。
- トップページのメタディスクリプションは2026-10-12にAIOSEOから設定、HTML出力に表示された。記事本文、テーマ、栞さん画像は無変更。
- 個別公開記事2件ではメタディスクリプションを実HTMLで確認済み。AIOSEOの投稿個別データが`description=null`でも、全記事のmetaタグ欠落を意味しない。
- 2026-10-12に大量REST読み取りの一部がHTTP507を返したため、**本番に反復APIクロールや一括書き込みはしない**。調査中: https://github.com/BL4GS/survival40-auto/issues/22 。

## 収益化の前に作る7つの読者導線
以下は**既存記事どうしをつなぐ編集案**。原稿内容を精査してから適所の前後文・リンクを決める。URLの一括検索置換や無関係なSEO目的リンクはしない。

1. **肌・老け見え**: `40s-male-aging-face-causes`（顔の老け見え）→ `40s-male-dark-spots-uv-care`（紫外線・シミ）→ `40s-male-sunscreen-how-to-choose`（日焼け止め）。必要なら`40s-male-all-in-one-skincare-guide`へ。
2. **髪・頭皮**: `40s-male-hair-loss-causes`（抜け毛の原因）→ `hair-tonic-vs-aga-treatment`（育毛剤と治療の違い）→ `online-aga-clinic-guide`（オンライン診療）。治療について断定や診療誘導をしない。
3. **ニオイ・清潔感**: `40s-male-body-odor-care`（体臭の原因）→ `40s-male-age-odor-care`（加齢臭対策）→ `40s-male-body-soap-odor-guide`（ボディソープ）。`40s-male-deodorant-guide`も適合するときに案内。
4. **口・歯**: `40s-male-bad-breath-care`（口臭）→ `40s-male-electric-toothbrush-guide`（歯ブラシ）/ `40s-male-mouthwash-guide`（洗口液）。`40s-male-tooth-stain-care`（黄ばみ）は別の悩みであり関係性を説明してから。
5. **睡眠・疲労**: `40s-fatigue-sleep-habits`（疲労・睡眠）→ `40s-male-waking-at-night`（夜間覚醒）→ `40s-male-pillow-how-to-choose`（枕）。症状を寝具で治せると断言しない。
6. **体型・運動**: `40s-male-belly-activity-fitness`（腹部・活動量）→ `40s-male-muscle-loss-home-training`（筋トレ）→ `40s-male-yoga-mat-home-training`（ヨガマット）。`40s-male-protein-how-to-choose`は食事との関係が妥当な場合に。
7. **入口の優先配分**: 固定トップ（紹介ページ）から上記の「悩みの全体像記事」7本へ、栞さんの案内と既存ページデザインを守りながら導線を整える。先に既存リンクの網羅性確認が必要。

## 配信初動
- 読者が何に悩んで検索するかに合わせ、上記の「原因・基本」記事を入口にする。
- SNSが使えるときは、記事をそのまま広告するのではなく、記事の中で実際に裏付けた**役立つポイントを1つだけ**紹介し、必要なら正規URLへ誘導する。
- 投稿アカウント・認証・プラットフォーム規約を確認するまでは、X/Threadsへの投稿を勝手に開始しない。
- Google Search Consoleで実際の検索流入、表示回数、検索語句、インデックス状況を測って優先順位を更新する。AIOSEOからGSCへの接続がOFFでも、既存GSCがある可能性は残る。
- 企画・執筆は既存のWordPress生成機構を再利用。広告の自動貼り付けは後回し。

## 当面のチェックポイント
1. HTTP507の再現性を低負荷で確認し、持続する場合はConoHaの容量/ログを診断。**ここが不安定なら自動記事運営をONにしない。**
2. Google Search Consoleでサイトマップ提出/取得状況を確認する。Search Consoleの接続・権限がなければ所有者へ後で**一度だけ**まとめて依頼。
3. 公開記事の実際の内部リンクを調べて上記7クラスタの欠けを明確化。ページ本文や栞の表示を守る。
4. まず1記事の安全な配信・検索評価を測り、量産しない。
5. SEOやSNSの進捗と、記事の安全な公開自動化の進捗は別軸で管理する。

## Homepage links updated on live WordPress (2026-10-12)
- Safely edited only WordPress static front page **post ID 471** via WPVibe exact server-side content replacement. Preserved the leading `[survival40_home]` shortcode and generated Shiori guide/theme. Appended a simple reader-facing heading **「気になるテーマをもう少し読む」** and nine previously unfeatured published article permalink links.
- Rechecked WordPress site response after the edit: published **23** / draft **16**, unchanged.
- Verified homepage rendered `<main>` contains **all 23 of 23** canonical published post URLs, plus existing Shiori guide (`s40-home-guide`) and category cards (`s40-home-card`). This is a URL coverage result, **not** a guarantee of mobile visual design, usability, Google indexing or article-body contextual crosslinks.
- The shortcode renderer currently emits an extra closing `</p>` before the new section. The HTML is rendered and links are present, but the markup warrants separate housekeeping. A follow-up safe block-formatter edit failed 422 without applying; **no attempt to bypass the validation was made**.
- The exact rollout and caveats are logged on https://github.com/BL4GS/survival40-auto/issues/24 .
- No published article bodies were edited, and no plugin auto-publisher/GitHub Release updates were triggered.

## Sitemap and Search Console readiness verification (2026-10-12)
- Authenticated WordPress GET via WPVibe confirms WordPress `blog_public=1`. AIOSEO `aioseo-audit/site-get` reports `sitemap_enabled=true` and index `https://www.survival40.com/sitemap.xml`; its `search_console_connected=false` means **AIOSEO is not linked to Search Console**, not necessarily that Google Search Console has no independently verified site property.
- Confirmed `sitemap.xml` lists `post-sitemap.xml`, `page-sitemap.xml`, `category-sitemap.xml`; its `post-sitemap.xml` holds **23** article URLs, `page-sitemap.xml` contains the canonical home page, and categories are included.
- Compared all **23 published canonical WordPress REST permalinks** to all **23 post-sitemap URLs**: exact one-to-one match; **no missing post and no duplicate URL** in the sitemap. This proves publishing/sitemap consistency, **not** Google indexation or impressions.
- Homepage `<main>` currently has a direct link to **23 of 23 public articles**, including the nine supplementary reader pathways added to WordPress page ID 471. Original Shiori guide and homepage cards persist.
- To measure actual Google queries, impressions, clicks and URL indexing, connect the user's existing Search Console property with an authorized analytics connection (GSC Wizard suggested through ChatGPT); do not assume a new property must be created until current Google account ownership is checked.
- Distinguish **site readiness** from the pending ConoHa restore/release blocker. Do not enable production auto-writing just because the sitemap is complete.

## Live GSC Wizard connection check (2026-10-12)
- GSC Wizard plugin is connected to a Google account with the **full** `webmasters` scope, but its only registered Search Console property at this time is `https://worker02.livedoor.blog/` (a **different site**).
- Tried registering all likely representations via GSC Wizard `add_site`: `https://www.survival40.com/`, `sc-domain:survival40.com`, and `https://survival40.com/`. All explicitly returned **not_found** in the Google Search Console account linked to GSC Wizard. No property was created and no site settings were modified.
- **Blocker:** User must either connect the Google account that already owns the Survival40 Search Console property, or register/verify the canonical `https://www.survival40.com/` URL-prefix property in Google Search Console using that Google account. Once visible there, use GSC Wizard `add_site`, then `get_site_summary`, `list_sitemaps`, `query_top_pages`, `query_top_queries`, and selective `inspect_url` (quota-aware).
- The existing home page meta `google-site-verification` token belongs to an unknown verification flow. Its presence **does not prove** that the currently connected Google account owns the property.
- **Do not attribute** the livedoor.blog GSC data to Survival40; do not fabricate traffic or indexation claims. Article sitemap and homepage links are verified independently.
