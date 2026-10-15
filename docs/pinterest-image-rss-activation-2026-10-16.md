# Survival40 Pinterest image-backed RSS — owner-authorized

## Verified, 2026-10-16 JST

- WordPress native `/feed/` returns HTTP 200 to GitHub Actions; `/wp-json/wp/v2/posts` returns HTTP 403 and must not be bypassed.
- Shiori's existing `assets/navigator/explain.webp` returns 200 to GitHub Actions.
- WordPress and Threads code have not been modified by this feature.
- Workflow `.github/workflows/pinterest-image-rss.yml` executes at 00:35, 06:35, 12:35, 18:35 UTC.
- Script `scripts/pinterest/build_rss.py` parses only verified public WordPress RSS items. It does not follow links to off-domain resources, and rejects unexpected tracking parameters.
- Successful full build: GitHub Actions run **38760524474**, 2026-10-16 JST.
- Output feed `pinterest/survival40-pins.xml` and original-art PNG `assets/pinterest/auto/512.png` confirmed as real repository files.
- Only one vetted legacy item (ID 512) is seeded; future items require publication from 2026-10-16 00:00 JST. Previously scheduled Metricool pin ID 393 excluded to avoid duplication.
- Static cards: Ghost White #F8F8FF, original Shiori guide on lower left, verified canonical article destination, no affiliate banner imagery.
- GitHub Actions refreshes the RSS; **this does not establish a Pinterest RSS subscription**.

## Why Metricool autolist must NOT consume ordinary WordPress RSS

Metricool help says autolists read image from the linked article's `og:image` (falling back to first page image), **not** from `<enclosure>` in the RSS. Original WordPress `/feed/` contains no item images and Metricool's tested preview showed an ALGO advertising banner. Never enable that original-feed autolist for Pinterest.

Do not use **both** Pinterest native RSS ingestion and a parallel Metricool autolist for the same article feed: duplicates would result.

## Pinterest native RSS connection — completed in owner UI (2026-10-16 JST)

The owner connected the verified `Survival40` business account's **native Pinterest RSS** through Pinterest Settings → コンテンツのインポート → RSS → ピンの一括作成 → RSSフィードをリンクする.

Feed URL retained in Pinterest's saved RSS configuration (visible alongside the **編集する** and **さらに追加する** controls):

`https://raw.githubusercontent.com/BL4GS/survival40-auto/main/pinterest/survival40-pins.xml`

Intended target is the public board `40代からの生存戦略`, previously confirmed with the owner. Do not connect a duplicate feed, add Metricool autolist, or request repeating this one-time setup absent a specific error.

Each RSS item has exactly one original Shiori artwork image in `<enclosure type="image/png" length="...">` and an article `<link>` under the verified `https://www.survival40.com/` domain. This is consistent with the [official Pinterest RSS specification](https://help.pinterest.com/ja/business/article/auto-publish-pins-from-your-rss-feed), which requires claimed-domain **item links**. The RSS file itself is hosted on GitHub and the connection was saved; nevertheless acceptance as a **published Pin** is still unproven.

**Do not conflate three separate statuses:**
- GitHub RSS generation **PASSED** (first full build `38760524474`; first subsequent scheduled run `38791814199`).
- Pinterest native RSS **CONNECTED** in the owner's Pinterest UI on 2026-10-16.
- First Pin created **from that RSS: NOT YET VERIFIED**. Target: older vetted article ID `512`, `40s-eye-strain-massage-breaks`; verify actual Pin ID, correct image and outbound URL. Pinterest may take up to 24 hours after RSS update according to its help.
- The separate Metricool one-off article ID `393` **IS VERIFIED PUBLISHED** (Metricool Pinterest provider status `PUBLISHED`, pin `1101411652652841054` at 2026-10-16 00:20 JST); do **not** mistake it for native RSS ingest.

If no RSS Pin appears after a reasonable ingestion period, diagnose the actual Pinterest state and the public XML/image/article links first. Do not silently republish items, edit article dates, backfill hundreds of old posts, or change claimed-domain verification. A same-domain RSS proxy would require a separate tested WordPress deployment with reliable Web/DB backup and rollback, not an unattended production plugin update.

## Operational tests

1. GitHub Actions scheduled run success, publicly readable RSS with current items and matching `<enclosure>` images.
2. Pinterest RSS connection confirmation and claimed-domain link validation.
3. First Pin rendered with Shiori and article link, no ad banner, no duplicate of prior Metricool post.
4. Next newly published article appears in the RSS within the next successful six-hourly run and subsequently on Pinterest.

Publication latency depends on GitHub Actions scheduling and Pinterest ingestion, normally about 24 hours after RSS changes according to Pinterest help.
