# Survival40 — organic distribution rollout checkpoint (2026-10-21 JST)

Status: source-controlled and test-verified changes have been merged; **actual platform delivery is not certified by tests**. `PROJECT_VISION.md` remains authoritative.

## Pinterest native RSS transport
- [Merged PR #106](https://github.com/BL4GS/survival40-auto/pull/106) adds a daily 11:00 JST read-only audit checking the exact owner-connected public GitHub RAW RSS XML and one matching original Pinterest image against the repository source bytes. It produces a time-limited diagnostic JSON artifact.
- CI [run 39446018958](https://github.com/BL4GS/survival40-auto/actions/runs/39446018958) passed offline security/source tests; it deliberately **did not make public GETs on the PR**.
- The source RSS was connected to Pinterest in the owner's account UI on 2026-10-16; do not reconnect or create a competing Metricool Pinterest autolist.
- Real native RSS Pin ID, source board result, image presentation and outbound article clicks **remain unverified**. A successful GitHub RAW HTTP fetch **cannot prove actual Pinterest Pin publishing**. Search engines not finding Pins is not definitive.
- Future scheduled run reports `RSS_AND_SAMPLE_IMAGE_TRANSPORT_OK`, `REMOTE_RSS_DIFFERS_REVIEW_CACHE_OR_UPDATE`, `REMOTE_IMAGE_DIFFERS_REVIEW` or `UNAVAILABLE_UNVERIFIED`. Cache delays, missing data or blocked transport should not be called Pinterest failures without provider evidence.

## 栞さん: limited one-for-one genuinely useful notes
- [Merged PR #107](https://github.com/BL4GS/survival40-auto/pull/107) adds a **no-publisher** overlay. The source and safeguards were fixed at immutable commit `8189c0900e137c6fcf572b301dfa600a45a09ca2`.
- [Merged PR #108](https://github.com/BL4GS/survival40-auto/pull/108) wires the review-only overlay into the existing four-slot `@survival40_jp` workflow. The original generator/publisher source remains pinned at `030e1f8a4cb23550802653b1dbcc97a263473566`, preserving Meta identity preflight and durable GitHub slot/article reservation.
- The strictly bounded pilot replaces **only the existing Thursday 16:00 JST everyday slot** on 2026-10-22, 10-29, 11-05 and 11-12, with one of four source-backed short notes on practical clothing/laundry/shoe tips. Posts are not added, other daily slots and article promotion calendar are unchanged; after Nov12 all slots return to the original everyday generator.
- Before replacement, the approved source needs an exact archived original article RSS title/description/image identity and a **fresh public HTML GET for its exact canonical article URL**, with at least two relevant body terms. A stale, missing, inaccessible, changed or differently addressed source keeps the already-generated ordinary Shiori draft. No external URL or affiliate marketing copy is inserted in the useful-note text.
- Additional user-facing publication is **not established** by PR tests: [GitHub Actions run 39447810724](https://github.com/BL4GS/survival40-auto/actions/runs/39447810724) passed offline tests for both immutable source trees and skipped actual publishing on PR. The first scheduled 16:00 run must confirm whether a helpful note passed the live-source gate and was published by the existing Meta ledger, or whether the ordinary fallback was published.
- **Rollback:** remove or disable the optional second approved-source checkout and one overlay execution step in `.github/workflows/threads-drafts.yml` in a reviewed GitHub PR. Keep all original pinned four-slot steps, scheduled cron/fallback and Meta publisher intact. Do not attempt to repost any slot already reserved.

## Discover image work status
- [Merged PR #104](https://github.com/BL4GS/survival40-auto/pull/104) remains a **disabled-by-default staging-only PHP AIOSEO filter simulation**, never installed or activated on WordPress.
- The source-controlled 1200×630 branded images are technically valid for sampled articles, but contain prominent overlaid headline text and are **not automatically recommended as Discover editorial hero images**. Prefer topic-relevant, high-quality, low-text approved original imagery after future editorial review. Any single-post WordPress featured/social image test needs backup, restore and independent staging verification, not bulk updates.
- Google Discover placement has no application and no guarantee. Search Console Discover impressions and GA4 social referral sessions are not currently verified via connected data.

## Preserve
No changes to the owner's personal Threads/X accounts, no new SNS posting volume, no Pinterest duplicate imports, no added subscriptions, no WordPress updates or WPVibe calls in this rollout.
