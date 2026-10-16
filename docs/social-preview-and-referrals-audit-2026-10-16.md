# Survival40 social card and attribution audit — 2026-10-16 JST

This is a **read-only production audit**. No changes to WordPress posts, plugins, AIOSEO options, analytics consent or any SNS settings have been made.

## Live article SEO/social metadata findings

WPVibe rendered read-only HTML for three *published* Survival40 articles:

- https://www.survival40.com/women-men-grooming-impression-survey/
- https://www.survival40.com/40s-eye-strain-massage-breaks/
- https://www.survival40.com/40s-male-belly-activity-fitness/

All three declare AIOSEO 5.0.3 Open Graph title, description, type and URL plus twitter:card=summary_large_image, but **none contained a meta property=og:image or name=twitter:image** in the head.

The survey article's JSON-LD BlogPosting image currently points to a 96x96 Gravatar author avatar, not to the original 1200x630 Shiori card.

**Implication:** A missing social-image field leaves social consumers free to choose another page image or none. This may explain why an earlier Threads article share preview showed an affiliate banner, but the exact image chosen by each social scraper must be independently verified. Do not claim the preview is fixed merely because a GitHub image exists.

## Existing safe branded image assets

- GitHub original article-specific Shiori OG art: assets/social/og/<WP-post-id>.png (1200x630) and Instagram image: assets/instagram/auto/<WP-post-id>.png (1080x1350).
- Metricool Instagram first post uses its own 4:5 media upload; it does not need an article Open Graph image.
- Pinterest's native RSS uses its own original image enclosure, independently of WordPress OG.
- DO NOT put an affiliate product banner in article OG image just because one exists in the post content.

## Proposed future fix — not authorized/deployed by this audit

1. Prove AIOSEO's supported API/UI for setting an individual post social image URL. First check whether an externally hosted GitHub raw asset is accepted and whether a Twitter/X image is also emitted; do not assume custom URLs are supported. A WordPress Media Library copy of the original 1200x630 image may be required for AIOSEO's own post-specific UI or WordPress featured media.
2. In an **isolated staging test** on ONE non-destructive test article, verify rendered head contains exactly one valid og:image with 1200x630 original article artwork and, if appropriate, corresponding twitter:image. Check that AIOSEO, existing canonical URL, social description, actual body layout and affiliate destinations remain unchanged.
3. Only after independent original-image provenance, site restore/rollback path and staging checks pass, consider a narrowly scoped production change. Preserve previously published permalinks and existing URLs. Never edit user-facing theme/plugin automatically merely to add the image.
4. Confirm actual platform preview by fetching a fresh share link (social preview caches may lag); do not treat metadata alone as proof social cards are refreshed.
5. AIOSEO's automatic metadata and its article schema should remain authoritative; do not inject a second competing OG generator.

## Actual web traffic / social referrals

The published survey article's head includes the Google Analytics tag (Google Analytics by MonsterInsights v11.3.0, GA4 gtag configured). This confirms tracking JavaScript is emitted, **not** that visits are collected or that GA4 data is accessible to the current client.

Read-only connected-account checks:
- GSC Wizard lists the verified Search Console site URL https://www.survival40.com/ for search queries/pages. **Search Console is not a social-referral session report**.
- GSC Wizard GA4 property discovery reported connected=false; the current GSC Wizard account has not granted Analytics scope. Consequently a real breakdown by Instagram / Pinterest / Threads is unavailable through this connector; do not report guessed counts or interpret a blank report as zero visitors.
- Metricool brand 7444916 has Instagram/Threads/Pinterest linked. Its separate Blog/website connection is absent in the user's screenshot; attempting website analytics returned empty/zero-like data that cannot establish actual WordPress traffic.
- Next evidence-based step would be to verify actual GA4 property and session_source / session_medium (or session source/medium breakdown) with authorized GA4 read access. This requires **one-time user consent** if no authorized account is available. Never silently change GA4, MonsterInsights, consent management or WordPress tracking configuration.
- Instagram profile bio currently links to the homepage per owner; because Instagram feed-caption URLs are not clickable, keep the bio CTA. To attribute traffic reliably, a deliberate **optional** separate tracked bio URL with utm_source=instagram, utm_medium=social may help; only after measuring existing data and avoiding duplicate canonical content or harmful tracking behavior.
- Native Pinterest RSS uses verified canonical article links. Keep them unchanged until a separate integrity review; don't add alternate duplicate Pins or feeds.

## Responsible next operation

Prioritize verifying the first Metricool Instagram scheduled post at 2026-10-17 10:00 JST and the first Pinterest *native RSS-created* Pin before enabling any second publisher. Production WP and social services unchanged by this audit.
