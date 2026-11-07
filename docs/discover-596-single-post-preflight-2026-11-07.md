# Article 596 Discover image: single-post preflight (2026-11-07 JST)

Status: **EVIDENCE ONLY / NO PRODUCTION CHANGE**. This is a non-deployable decision record, not approval to change AIOSEO, WordPress, PHP, or social posting. Canonical editorial direction: [PROJECT_VISION.md](../PROJECT_VISION.md); production safety gate: [release-01921-production-safety.md](release-01921-production-safety.md); rollout constraints: [organic-distribution-rollout-2026-10-21.md](organic-distribution-rollout-2026-10-21.md).

## Exact target and authenticated read-only evidence (2026-11-07 JST)

- WordPress post ID: **596**; status: **publish**; slug: `40s-winter-dry-air-humidifier-guide`; canonical: https://www.survival40.com/40s-winter-dry-air-humidifier-guide/
- WordPress REST post metadata: **featured_media = 0** (no featured attachment). This was a read-only authenticated GET, not an update.
- Rendered article HTML obtained through the connected site's read-only page inspection: `max-image-preview:large` present; `og:image`, `og:image:secure_url`, and `twitter:image` all point to `https://raw.githubusercontent.com/BL4GS/survival40-auto/main/assets/instagram/auto/596.png`.
- AIOSEO `BlogPosting.image` is a **96×96 Gravatar** rather than an article image. AIOSEO is responsible for the existing metadata; do not add a second independent set of OG tags.
- [Merged PR #135](https://github.com/BL4GS/survival40-auto/pull/135) verified *repository PNG IHDR dimensions*, not public delivery: `assets/social/og/596.png` = **1200×630**; Instagram = **1080×1350**; Pinterest = **1000×1500**.
- **Not verified:** public HTTP 200/content-type/body for the image URLs, Googlebot accessibility, Google Discover impressions, original 1200×630 card's editorial suitability, WordPress media-library upload, actual Google image selection. The 1200px file is a candidate, not an approved Discover hero.

## Decision and safety gates

1. **Do not change the live article yet.** Existing 1200×630 branded cards can contain prominent overlaid headline text; width alone does not establish editorial suitability for Discover. Inspect the actual pixels, licensing, relevance, cropping, and text overlay first. Prefer an approved topic-relevant, low-text image.
2. Before any single-post change, verify the chosen image via an unauthenticated HTTP GET (status 200, correct image MIME, actual dimensions >=1200px wide), public crawlability and robots restrictions. The current read-only HTML inspection does not establish these facts.
3. Capture a current full site backup and a restorable rollback path; save the article's current `og:image`, `twitter:image`, schema image, featured_media, post status, slug, internal links and existing ad markup. Do not treat a GitHub commit as a WordPress backup.
4. In an **isolated staging clone**, test only post 596 with the existing AIOSEO integration, comparing rendered HTML before/after: one canonical, one coherent `og:image`/secure URL, matching `twitter:image` and `BlogPosting.image`, no Gravatar/ad banner as the article image, `max-image-preview:large` retained, no duplicate tags.
5. Only after separate production authorization and verified backup/restore should an approved **single-post** correction be considered. Confirm live rendered HTML and actual image GET again. Roll back the exact post-level media/SEO fields from the captured snapshot if validation fails; verify status, links, ads, schedules, and SNS ledgers remain unchanged.
6. Never change sitewide AIOSEO defaults, WordPress plugin release/version.txt, PHP, ConoHa, DB, themes, SNS connectors/slots, Pinterest RSS imports, ads, scheduled posts, or DiGlife as part of this experiment.

## Adjacent backlog and measurement

- Existing OG/schema diagnostics: post IDs 387, 389, 438, 596; post 596 is the only confirmed local 1200px OG candidate in PR #135's three checked directories. Do not extrapolate to other storage paths.
- Post 421 (electric toothbrush) and 412 (home training) were also reported to lack a suitable featured/social image; this record **does not** assert a full-site audit.
- Search demand/traffic, Discover impressions, Pinterest actual Pin IDs, Instagram/Threads deliveries, and affiliate conversions were **not measured** here. GSC Wizard currently returns `payment_required`; do not convert absence of measurement into zero traffic.
- No article body, ad, category, status, URL, scheduled automation, or WordPress configuration was modified in this checkpoint.

Rollback of **this documentation-only PR**: close the PR or revert the single Markdown commit; no runtime or production changes were made.
