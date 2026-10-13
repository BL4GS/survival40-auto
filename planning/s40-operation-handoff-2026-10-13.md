# Survival40 operational handoff — 2026-10-13 JST

This file is a **snapshot**, not a source of truth for future live status. For any new work, read live WordPress, GitHub Actions and the current A8 account before editing. It exists to preserve decisions and exact identifiers between ChatGPT threads.

## Editorial direction
- Site: https://www.survival40.com/ (WordPress, plugin Survival40 Auto 0.19.20 as of 2026-10-13).
- Audience: men in their 40s; grooming, diet, sleep, fatigue, exercise, seasonal everyday issues. Useful content first; no guarantee of medical outcomes.
- Daily one **new** fact-checked article, ideally ~1,800–3,000 Japanese characters, with primary-source links and clear population/date/conditions for survey data.
- Friday preference: one research/survey article about women's impressions or related grooming concerns, acknowledging sampling limitations.
- The ChatGPT scheduled task runs ~09:00 JST to research/write. Beginning **2026-10-19**, new daily article publication is targeted for **21:00 JST** using WP future status. This is a ChatGPT task, **not** GitHub Actions; its real-world reliability must be checked after the first run. Avoid duplicate posts if one exists for that date. Earlier dates use the existing earlier schedule.
- Articles or services are not published if source validation fails. Do not invent first-person consumer experiences.
- Product links are optional; do not force affiliate advertising into unrelated topics.

## Known posts and exact status (at snapshot)
| WP post ID | Status at 2026-10-13 | Publication date (JST) | Slug | Topic |
|---|---|---|---|---|
| 512 | publish | 2026-10-13 18:21 | `40s-eye-strain-massage-breaks` | Eye strain, screen breaks and massage limits |
| 514 | publish | 2026-10-13 18:24 | `40s-fatigue-food-meal-balance` | Fatigue and food choices |
| 516 | future | 2026-10-16 07:00 | `women-men-grooming-impression-survey` | Women's views on men's grooming, with actual survey sampling |
| 518 | future | 2026-10-19 21:00 | `40s-year-end-party-morning-after-care` | Seasonal year-end gathering, alcohol and next-day rest; owner-approved A8 酒長快朝 banner |
| 530 | future | 2026-10-20 21:00 | `40s-alcohol-after-strength-training` | Alcohol after resistance training, including a high-dose study and its limits |

Never turn a future post into published ahead of its time. Verify WordPress future post cron, actual status and public page after scheduled date. As at the snapshot `publish_future_post` WP-Cron events were present.

## Threads / Shiori
- Account: `@survival40_jp`, character 栞 (Shiori), **not** BL4GS characters Iroha/Mashiro.
- Scheduled everyday posts at **08:00 and 20:00 JST** daily. Initial 2026-10-13 20:00 post succeeded; GitHub Actions run 38388934540 and published ledger `state/threads-ledger` key `2026-10-13-evening`. The owner observed initial engagement and ~117 impressions early on; views are not unique people.
- Previously fixed 20:00 promotional posts on 2026-10-14/17/21/24 remain as set, replacing the usual evening post on those 4 dates.
- From 2026-10-19, **an additional** 22:00 JST daily article-introduction GitHub workflow applies only if today's genuinely published 21:00 article can be verified via public WP REST. Nothing to post if the article is missing, late, or not public. Ledger deduplicates article identities. The 08:00 and 20:00 posts continue independently.
- Production workflows: `.github/workflows/threads-drafts.yml` and `.github/workflows/threads-late-article.yml`. The reviewed source is pinned at commit `2c6660b3856fd87e3d04583dd6c4f273020a0c17` in draft PR #34. Do not assume the pinned source updates automatically.
- GitHub runs are best effort; actual 22:00 delivery still requires live verification after Oct 19.

## A8 paid placements and guardrails
- Canonical owner-supplied creative list: `planning/a8-banner-assets-unified-2026-10.json` (16 A8 programs).
- Confirmed approved added program: `planning/a8-approved-ads-additions-2026-10.json` (酒長快朝 `s00000027703001`), owner confirmed instant approval; food/supplement, **not a medicine**. No claims of hangover cure or prevention.
- **Placement ledger**: `planning/a8-live-post-placements-2026-10.json`. On 2026-10-13 this has **6** live articles with manually inserted A8 banners and **1** scheduled article with an A8 banner; **4** newly inserted contextual internal links.
- Live A8 post IDs: 450 (ULTORA), 438 (NULL all-in-one), 442 (Premium Black Shampoo), 514 (DELISH KITCHEN Meals), 400 (RingConn), 387 (My Pillow/マイまくら).
- Program `s00000022947002` remains disabled/uncertain. Use only advertiser-relevant original A8 links and banners; mark PR, rel=nofollow sponsored, do not claim unsupported health or cosmetic outcomes.
- **Important distinction:** Live banners were inserted manually into relevant WordPress `post_content` with WPVibe's exact-match `/wpvibe/v1/content/edit` and visibly verified. This is NOT the same as enabling Survival40 Auto's staged global automatic banner renderer. The live plugin remains v0.19.20 and the automatic affiliate rollout is still OFF. Do not stage/deploy new plugin builds casually (prior update/deactivation concerns), and do not overwrite WP option `s40_affiliate_ledger_v1`.

## Operational safeguards
- Keep DiGlife, theme, other content and production plugin deployment untouched unless separately requested.
- When editing large text, prefer WPVibe content/search and content/edit exact-match to whole-body REST rewrites; verify the post afterwards and check rendered HTML.
- Once during 2026-10-13 there was an intermittent WPVibe REST 507 Insufficient Storage response; a later GET succeeded. This is not proof of permanent hosting exhaustion. If 5xx recurs, stop writes and check connection/origin.
- Be explicit about whether work is **saved to GitHub**, **written in WordPress as draft/future**, or **actually public and verified**. Never conflate those states.
- When a conversation changes, start by consulting live source and this handoff and the placement ledger, before asking the owner to resend ads or repeat prior instructions.
