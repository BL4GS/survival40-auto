# Pinterest automatic publishing — implementation contract

Status: **PARTIAL / NOT LIVE** (2026-10-15). Pinterest domain is verified and the first board was created and switched to public, as confirmed by the owner. Owner requested automatic Pinterest publication from Survival40 after successfully claiming https://www.survival40.com/ in Pinterest. This document records evidence and the safe integration route. Connecting a domain is **not** the same as activating automatic Pins.

## Objective

Once a suitable Survival40 article is automatically published, create a relevant, original Pinterest image and metadata, expose them in a compatible RSS 2.0 feed, and let Pinterest's built-in RSS importer place Pins on a public board leading readers to the exact article URL. **No routine owner posting, per-article editing, API token management or manual campaign selection.** Pinterest should remain another traffic channel for the same reader-first site, not change the WordPress layout or Shiori's role.

## Evidence collected 2026-10-15

- Pinterest owner screenshot reports website **connected successfully** at `www.survival40.com`; AIOSEO `webmasterTools.pinterest` was saved and `<meta name="p:domain_verify" ... />` was verified in the rendered live homepage head.
- Verified WordPress feed URL: `https://www.survival40.com/feed/`. WPVibe returned valid-looking **RSS 2.0** XML with correct domain article links, titles, descriptions and 10 items; `posts_per_rss=10`, `rss_use_excerpt=1`.
- **Blocking issue:** sampled RSS items had **no item-level `<enclosure>`, `<media:content>` or `<image>` element**. WP REST's 15 latest published posts (including posts 585, 581, 533, 514, 512) all reported `featured_media=0`. The channel-level site icon does not satisfy the required **item-level** artwork.
- Pinterest's official guidance: an RSS feed can auto-create Pins within 24 hours of new feed content; it reads item-level `image` / `enclosure` / `media:content` for images and item `title` / `description` for text; every item must link to the claimed domain. RSS 2.x is supported. See https://help.pinterest.com/ja/business/article/auto-publish-pins-from-your-rss-feed and https://help.pinterest.com/en/business/article/import-content-to-pinterest .
- The user created the Pinterest board **「40代からの生存戦略」** and explicitly confirmed changing it from secret to **public**. This is user-confirmed, not independently checked through Pinterest API.
- **No RSS auto-publish connection has been enabled on Pinterest as part of this development task**. That setting lives in Pinterest's signed-in web interface and requires selecting a destination board.

## Owner-approved visual template (2026-10-15)

- **Canvas:** portrait 1000 × 1500 px, 2:3 ratio.
- **Background:** use the same **Ghost White / ゴーストホワイト (#F8F8FF)** as the Survival40 blog's intended background color. Keep it uniform across the default Pin series; **no photo background, gradient or decorative AI-like graphics by default**. Before a production renderer ships, compare the live site's actual computed background color and adjust only if the site's token differs from #F8F8FF.
- **Guide:** place the existing licensed/owned **栞さん "こちら" explanation/gesturing pose at the lower left**. Reuse the source asset, identity, clothing and natural expression; do not regenerate a lookalike or change the character design. Do not crop hands/face awkwardly. This consistent placement helps identify Survival40 in Pinterest's image grid.
- **Copy:** make the article's specific reader question/topic the largest element, positioned upper/central with clear space away from the guide. Natural Japanese titles without the mechanical "｜" separator; shorter phrasing is allowed only if true to the article. Use a dark, high-contrast font against Ghost White with no crowded text.
- **Branding:** small "Survival40" / 「40代からの生存戦略」 credit toward the bottom; never make it look like an ad. No A8 image, sales CTA, fake endorsements or site favicon as the main visual.
- **Automation:** one consistent template as the starting default. Font size and line wrapping adapt to varying titles, and accessibility checks should ensure it remains readable in a small mobile Pinterest grid. No mandatory per-category backgrounds or further owner design approvals.
- **Status:** template direction approved in chat, **not yet implemented as generated images or wired to Pinterest RSS**. Do not claim these Pins are live.

## Design and safety requirements

1. Prefer Pinterest's first-party **RSS importer**, not a third-party scheduler or an unapproved direct Pinterest API integration. This avoids storing Pinterest credentials and posting API quotas.
2. Each eligible published article needs **one appropriate permitted image**. The image should be article-specific and recognizably Survival40, suitable for vertical Pinterest presentation (aim for 2:3 aspect ratio); use established licensed/owned Shiori visuals only where contextually appropriate. No generic website favicon, affiliate banners, automatically hotlinked marketplace images, unlicensed photos or fabricated first-hand product results as substitute artwork.
3. **Do not publish a feed item without a genuine eligible image**, do not point Pinterest at an incomplete feed, and do not take the site's ordinary RSS hostage. If generating images fails, postpone the Pinterest feed item; WordPress publishing continues safely.
4. Titles and descriptions follow `PROJECT_VISION.md`: natural Japanese without formulaic fullwidth bar separators by default; real reader search intent; no fear-mongering or unsupported medical claims. No automatic ad copy, affiliate image reuse or false AI-as-human authorship.
5. Article link goes to the claimed `https://www.survival40.com` host (not directly to an affiliate store); use stable URL / GUID deduplication and ensure each eligible article generates at most one intended Pin. Ensure site indexing and published status. Never expose drafts, scheduled, private or failed-quality content.
6. Prefer a **Pinterest-specific feed** if needed to preserve standard RSS behavior. Avoid surprise backfill floods of already published posts when first connecting; agree activation start boundary, or perform an intentional batch separately.
7. Respect user decision: one initial *public* Pinterest board can be used; themed boards/category feeds may be introduced later only if valuable. Do not create 8 boards as a prerequisite or require routine manual board selection.
8. Fail closed on empty feed, missing image, wrong host, malformed XML, duplicate GUID, unreachable image or accidentally private board. Protect WordPress articles, SEO, existing assets, scheduled posts, ads, 栞さん visual placements and site layout.
9. GitHub CI/sandbox simulation before release; actual WordPress production release **still blocked** by `docs/release-01921-production-safety.md`. Do not bypass backup/rollback/real-site verification or claim GitHub code is live. Evaluate the simplest safe, isolated integration route instead of widening an unsafe update.
10. Verify success in three layers independently: (a) actual public feed item contains image/title/link, (b) Pinterest UI confirms RSS feed connected to public board, and (c) Pinterest displays a real Pin linking to the right post. RSS availability alone does not prove auto-posting.

## Next execution steps

- Stage a safe automatic per-article image generation method with independent tests, and render it in a Pinterest-compatible dedicated RSS feed without modifying current live articles or their URLs.
- Establish safety and restore baseline, deploy only the reviewed change with explicit owner approval.
- In Pinterest desktop UI use **Settings → コンテンツのインポート** (or **ピンの一括作成**) → RSS link, provide the proven feed URL, select the public board, and save.
- Verify a single end-to-end Pin, correct attribution, destination, and no duplicate / affiliate-only graphic. Then leave the feed autonomous.

**Current completion:** Pinterest site claim DONE; public destination board user-confirmed DONE; live RSS assessed; blocker identified; automatic image generation, Pinterest feed with art, in-app RSS connection and end-to-end posting all NOT DONE.
