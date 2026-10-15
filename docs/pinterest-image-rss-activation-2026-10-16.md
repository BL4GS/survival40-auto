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

## One-time user-controlled Pinterest connection required

Pinterest business account `Survival40` claims `www.survival40.com`; its public board is `40代からの生存戦略`.

Go to Pinterest web desktop: Settings → ピンの一括作成 (Create Pins in bulk) → RSS フィードをリンクする → input:

`https://raw.githubusercontent.com/BL4GS/survival40-auto/main/pinterest/survival40-pins.xml`

Choose public board `40代からの生存戦略` → Save.

Only one image is included per RSS item. Each item `<link>` is a canonical claimed-domain URL. Source image appears in each item `<enclosure type="image/png" length="...">`; this is supported by Pinterest's [official RSS specification](https://help.pinterest.com/ja/business/article/auto-publish-pins-from-your-rss-feed).

The Pinterest official UI has to accept this cross-domain-hosted XML feed. **Do not report production auto-publishing active until Pinterest confirms RSS connection and a real Pin linking to a correct article is observed.** If refused because the RSS URL is hosted on GitHub rather than the claimed WordPress domain, do not repeatedly retry or change security settings; propose a safely staged same-domain feed proxy with release/rollback gates.

## Operational tests

1. GitHub Actions scheduled run success, publicly readable RSS with current items and matching `<enclosure>` images.
2. Pinterest RSS connection confirmation and claimed-domain link validation.
3. First Pin rendered with Shiori and article link, no ad banner, no duplicate of prior Metricool post.
4. Next newly published article appears in the RSS within the next successful six-hourly run and subsequently on Pinterest.

Publication latency depends on GitHub Actions scheduling and Pinterest ingestion, normally about 24 hours after RSS changes according to Pinterest help.
