# Survival40 Threads operation — Shiori

## Brand and channel
- Threads account: **@survival40_jp**, persona **栞さん**, separate from BL4GS characters (いろは and ましろ).
- Audience: primarily men in their 40s interested in manageable self-care, lifestyle, grooming, health and seasonal topics.
- The account builds readers' trust through useful and unpretentious information; never use authoritarian, lecturing, guilt-inducing copy.
- Do not claim Shiori has real personal experiences, licenses, first-hand product use or medical expertise she does not have.
- Avoid repeating the identical greeting daily or manufacturing engagement through unsolicited replies/likes/follows.

## Publication plan approved by owner (2026-10-11)
1. **08:00 JST** (morning): a short friendly greeting, light seasonal / ordinary-life fact only if grounded. No automatic links or affiliate claims.
2. **20:00 JST** (evening): a warm sign-off or simple non-intrusive question. No forced links or affiliate claims.
3. **Articles**: when Survival40 publishes a verified article, repackage its takeaway as a distinct, useful Threads post; include a real canonical link if appropriate. Do not promote all articles or copy sensational headlines.
4. Owner's personal Threads interactions stay personal; never auto-reply, auto-follow or mimic personal conversations.

## Current implementation
- `scripts/threads/compose.py` creates a **draft only** using the existing Gemini secret (`GEMINI_API_KEY` or `GOOGLE_API_KEY`) and a bounded free-tier model.
- `.github/workflows/threads-drafts.yml` runs at UTC 23:00 / 11:00 = JST 08:00 / 20:00; GitHub schedule is best-effort and may run late. Script skips the wrong local hour instead of publishing stale greetings.
- Drafts are saved to GitHub Actions artifacts for 14 days; no Threads access token is read or needed.
- `scripts/threads/test_compose.py` verifies slot selection and basic safety checks.
- Initial manual smoke test run `38139184153` passed generation, validation and artifact upload. The resulting post had `publish=false`.
- No automated publication, Threads token or WordPress article-to-Threads feed is connected yet.

## Requirements before live autopost
1. Meta app with the **Threads** use case, account-authorized OAuth 2.0 and suitable publish permissions such as `threads_basic` and `threads_content_publish`, per current Meta documentation.
2. Keep credentials in GitHub Secrets, never public files, URLs, Actions artifacts, prompts, or logs. Implement token refresh and explicit expiry/error monitoring.
3. Implement idempotency across delayed/retried schedules: one persistent key per local date + slot, and validate remote publication status before retry. Prevent double-posting if a first API publish succeeded but response was lost.
4. Validate the correct Threads user/account ID before any post. Prevent publishing from the owner's personal account.
5. Use the official Graph API for container creation/publication, not browser automation or unofficial password/session scraping.
6. Fail closed on API/permission/quota errors; no retry storm and no paid Gemini fallback.
7. Maintain a global emergency pause flag, content validation and a reliable audit log of accepted/skipped/error/published events.
8. Run a single explicitly authorized live test, review it on Threads, and only then enable scheduled posting. Do not turn on posting by changing a default accidentally.
9. Respect Meta's current API terms, rate limits, privacy rules and app/account eligibility.

## API reference
- Meta-maintained API collection: https://www.postman.com/meta/threads/collection/dht3nzz/threads-api
- Meta Threads documentation: https://developers.facebook.com/docs/threads

## Vision
Read `PROJECT_VISION.md`: reader-first, advertising optional and no mandatory daily user work. Paid ads are not part of the plan. Publishing more is not success unless it earns trust and useful engagement.
