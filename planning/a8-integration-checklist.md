# Survival40 A8 integration gate (staging)

## Verified inputs
- 16 owner-provided A8 HTML banner snippets have been normalized into `planning/a8-banner-assets-unified-2026-10.json`.
- All 16 use 300×250 image creatives, A8 click links and matching impression tracking codes.
- Treat the confirmed canonical IDs as `s00000021719001` for ULTORA and `s00000007191012` for Premium Black Shampoo; the WordPress seed currently uses `ultora` and `s0000007191012` and must be reconciled without overwriting stored notes/URLs.
- `s00000022947002` is a separate four-hour cleaning service, not house-cleaning 110. Its advertiser and approval terms are not verified; keep disabled.

## Deployment gates
1. Back up the saved WP option `s40_affiliate_ledger_v1` before any ID-key migration; retain all user-entered URLs, notes and status.
2. Register all 16 creatives as private ledger data with explicit ASP `A8`, program ID, creative type and campaign restrictions. Do not put ad code on arbitrary posts.
3. Ensure links use `rel="nofollow sponsored"`, an adjacent `PR` disclosure, and original unmodified A8 click/image/impression URLs. No impression beacon on admin preview, unpublished post or hidden image.
4. Leave new four-hour cleaning campaign disabled until owner confirms campaign approval and rules. Verify campaign-specific products (RingConn Gen 2 only, NULL gel only, etc.).
5. Implement article-type matching separately; an unsupported/mismatched article or no verified ad must have no affiliate banner.
6. Fix plugin update deactivation **before release**; current 0.19.20 runs on the live site and Github main release workflow must not be changed to invoke staging scripts prematurely.
7. Test PHP lint, WordPress staging activation, retained option data, update/active state, empty URL behavior, ad disclosure, mobile display, and WordPress error log.

**Current state:** Prepared only. No staged patch is included in `.github/workflows/release.yml` and no release version has been bumped.
