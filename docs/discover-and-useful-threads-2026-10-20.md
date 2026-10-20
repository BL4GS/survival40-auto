# Survival40 — Discover visibility and useful Shiori posts (2026-10-20)

Status: owner direction accepted in conversation; **implementation is incremental, not a claim of Discover placement or new live posting**. `PROJECT_VISION.md` is authoritative if there is any conflict.

## Objective
Stop relying only on users actively searching. Keep search as a durable channel, while strengthening *interest-based discovery* (Google Discover and Pinterest) and useful native Threads publishing under 栞さん's existing identity. The owner's personal X/Threads profiles remain personal and unmodified. Do not create new daily work.

## A. Google Discover: operational facts and guardrails

Official Google documentation:
- https://developers.google.com/search/docs/appearance/google-discover?hl=ja
- https://developers.google.com/search/docs/appearance/google-images?hl=ja

1. Content indexed by Google and compliant with Discover policies is **automatically eligible**, without application, special Discover markup, or guaranteed placement.
2. Article titles should be informative and natural, not sensational or misleading.
3. Google recommends relevant high-quality images at least 1200 px wide and over 300,000 total pixels, with sufficient landscape cropping room; use `max-image-preview:large` or AMP. Use a representative `og:image` or schema image to help Google select the preferred image. Avoid generic logos and overly text-heavy cover art.
4. Published articles may be selected even when older; do not stamp fake freshness, invent testimonials, write dubious medical promises, or change canonical URLs for Discover.
5. Search Console's Discover performance section may appear only after sufficient impressions. A missing report **does not prove ineligibility**.

### Existing implementation and current gap
- Original brand social assets can be generated in GitHub, but image files by themselves **do not add WordPress `og:image` metadata**.
- The existing `scripts/social/check_og.py` daily 10:25 JST workflow is read-only and inspects the public HTML of up to ten items already in the verified Pinterest RSS.
- This PR extends its same fetched HTML head to report HTML robot preview hints, `og:image` count and declared dimensions as **observations**, not claims about the image's actual bytes or Discover eligibility.
- HTML `meta` cannot detect the HTTP `X-Robots-Tag`, schema images, search index state, or live Google Discover impressions. The report explicitly labels these unverified.
- Any future change to AIOSEO's metadata, WordPress media/featured images or `max-image-preview` must first be isolated, independently backed up and regression-tested. Only the existing SEO component should emit these tags; **never inject competing duplicate metadata**.
- Do not replace site layout, Shiori visual identity, or live affiliate banners in the article to solve the card-preview problem.

### Future release checkpoint (separate PR)
A staging-only proof on one safe article should verify original image provenance, proper public image URL, 1200px+ true dimensions, matching title/body, existing AIOSEO output, canonical URL, front-end view and precise rollback. Don't switch all posts without evidence. Monitor Search Console Discover data when available. **No automated promise of placement.**

## B. 栞さん Threads: use more of the existing reach without turning her into an advice bot

The existing scheduled workflow publishes to verified `@survival40_jp` in its four daily slots and a separate, source-checked nightly article mention. **The 4-slot workflow checks out immutable SHA `030e1f8a4cb23550802653b1dbcc97a263473566`**, so a change to main's `threads/editorial.json` or `scripts/threads/compose.py` alone has **zero proven effect on live copy**. Never silently swap pinned refs or issue live Meta posts to test tone.

Editorial principle: keep ordinary comments, small personal quirks, occasional dry humor, and existing natural Japanese voice. Add **some** genuinely useful short notes, not a generic tip to every post. No forced questions, exaggerated empathy, three-step "self-improvement" templates, or recurring "save this" engagement bait. No automatic increase in post slots and no login/use of owner's personal account.

### Grounded helpful notes
- Prefer **one concrete detail per informative post**, from an actually published and reviewed Survival40 article or a reliable primary source, with provenance kept in the *private audit/preparation record*. Do not fabricate scientific facts, brand-use experiences, buyer testimonials, age/relationship experiences or medical outcomes.
- An example of a grounded topic, *not an auto-post approval*: when choosing a home-exercise mat, there is a difference between grip and thickness; explain what matters for a specified use case without asserting a favorite product.
- A topic can be useful without an outbound link. Where the actual article genuinely expands the point, link it sparingly, with a correct canonical URL and clear advertising disclosure when required.
- Source data unavailable, questionable claim, duplicate topic, or awkward voice -> **skip the informative proposal** and keep approved ordinary posting, not invent an unsourced tip.
- Keep a deliberate mixture: natural day-to-day observations, useful notes, and independently checked published article summaries. Do not convert all four everyday slots into product promotion.

### Shipping sequence
1. Produce credential-free samples from verified source material, run voice/persona and accuracy checks offline.
2. Validate the examples against the existing pinned scheduled generator, duplicate reservation ledger, fixed account identity, and separately verified article links.
3. Introduce a source-backed informative mode without new post volume, preferably in isolated previews, and enable live only after confirming the current publishing gate uses the reviewed code. No unreviewed auto-switch.
4. Track the actual outcomes: post views, engagement, link clicks / website sessions when Analytics access exists. Do not equate social views with traffic.

## Protected invariants
No WPVibe use for normal development. No WordPress writes, no media/SEO/plugin changes, no SNS account switches, no marketing on the owner's personal profiles, no additional recurring fees, and no new release until restore guarantees are verified.


## Verified implementation checkpoint — 2026-10-20 23:40 JST

### Discover/social cards
- Read-only social OG workflow run [39355845878](https://github.com/BL4GS/survival40-auto/actions/runs/39355845878) found **10/10 sampled published articles declare an og:image**, pointing to the site's same-article original `assets/instagram/auto/<id>.png` files (post IDs 599, 601, 606, 607, 608, 609, 610, 616, 617, 518).
- This supersedes the **older** October 16 observation that three other previously sampled articles had no OG image: different sample/time. **Do not claim current site-wide OG coverage from either sample.**
- [Merged PR #98](https://github.com/BL4GS/survival40-auto/pull/98) teaches the read-only auditor to classify those known original portrait images separately rather than mark them as unknown. Real pixel width is **not** checked by that HTML audit. Instagram artwork is intended for a 1080px-wide portrait layout, which must not be assumed to meet Google's 1200px-wide recommendation. Future WordPress/AIOSEO image selection remains a separate, backup-gated stage.
- [Merged PR #97](https://github.com/BL4GS/survival40-auto/pull/97) now inspects `max-image-preview` in HTML metadata without inferring Discover eligibility, impressions or Google indexing from this.
- The first *post-merge* scheduled audit evidence and any actual Discover performance are not yet reviewed; no WordPress image, SEO plugin, canonical or theme data was modified.

### 栞さん's helpful note rollout
- [Merged PR #99](https://github.com/BL4GS/survival40-auto/pull/99) adds four hand-reviewed, source-gated practical-note drafts derived only from verified same-article title, description and image identity in GitHub's Pinterest RSS: clothing size, laundry odor, clothing quantity, shoe odor. Generated output is `publish:false` and requires independent live-post verification before any social publication.
- GitHub Actions now has a no-token/no-network weekly Monday 07:15 JST **preview-only** workflow; two PR CI workflows succeeded before merge. It does **not** use Gemini, access Meta or update any of the existing 08/12/16/20/22 Threads posts. This feature adds no new audience-facing publication yet.
- The existing daily four-slot poster uses an immutable pinned source SHA. Changing copy preferences on main by itself **cannot** change the live posting. A future replacement of one existing slot needs source, duplication, Persona and publishing-gate tests first.

### 22:00 article-introduction resilience
- Separate existing workflow was failing on Oct 19–20 with `STOP: Too much article data; no automatic retry`. The pinned article source's public WordPress REST request fetched **40 full article bodies** with a 600 KB response cap.
- [Merged PR #100](https://github.com/BL4GS/survival40-auto/pull/100) retains the reviewed immutable checkout, cap, credentials, identity checks, and at-most-once ledger; in the ephemeral workflow runner only, narrows the public query to **the latest eight** posts. Tests succeed; PR execution deliberately skips WordPress GET and Meta publication.
- Next scheduled execution must verify the response is within limit and the correct published article is selected. This correction is not proof that every future payload will fit. No Threads post was sent as part of the PR.


## Follow-up: actual local Discover image validation — 2026-10-20

- [Merged PR #102](https://github.com/BL4GS/survival40-auto/pull/102) installs a **read-only local image integrity and source mapping verifier**, using the original images and already installed Pillow; no WordPress writes and no new publisher.
- [GitHub Actions run 39441733295](https://github.com/BL4GS/survival40-auto/actions/runs/39441733295) passed **30 offline regression tests** and fully decoded **10** original article image pairs from the verified current Pinterest feed. For these exact ten pairs, the local original landscape images are **1200×630** and the portrait Instagram originals are **1080×1350**. A 14-day evidence artifact is uploaded from the test run.
- The verified number is the **ten feed entries in that run**, not every article on the WordPress site, not necessarily every asset present in the GitHub tree. The images are candidate assets only; **actual public raw GitHub delivery was not fetched by this verifier**.
- On the next scheduled Instagram asset-generation workflow, the same verification runs **after generating images and before committing them** to GitHub, failing closed if the feed, manifest, article URLs or decoded PNGs disagree.
- The site's previously observed live Open Graph images use the portrait `assets/instagram/auto/<id>.png`, which are 1080px wide by the generated original asset design. **No WordPress `og:image` or AIOSEO settings were changed** to the existing 1200px landscape candidate images. The test does not certify actual Google Discover appearance, image aesthetics or Google indexing. Original 1200px social cards have substantial overlaid headline text; assess their visual suitability and Google's imagery guidance before a live rollout.
- Next SEO/Discover step (separate and **backup-gated**): verify AIOSEO-supported image selection and HTTPS image accessibility in staging for just one published article without duplicate OG tags or permalink changes, then inspect rendered live HTML and social previews. Do not promise Discover placement or enable bulk changes merely because offline PNG tests passed.


## Follow-up: active discovery, distribution and stage-only AIOSEO correction (2026-10-20)

### Stage-only Discover image replacement
- [Merged PR #104](https://github.com/BL4GS/survival40-auto/pull/104) repairs the disabled-by-default AIOSEO test snippet: for two exact preverified article IDs and URLs, the **known original Instagram 1080×1350 image** can now be replaced in the mock by the **known 1200×630 original social card**. Other owner-set OG/Twitter images, conflicting dimensions/source values and original titles/descriptions are preserved.
- [GitHub Actions run 39443499918](https://github.com/BL4GS/survival40-auto/actions/runs/39443499918) passed PHP syntax and offline filter/opt-in tests. This is **NOT deployed to WordPress**, and does not prove the installed AIOSEO configuration or social preview behavior.
- AIOSEO officially documents its `aioseo_facebook_tags` filter and per-post custom social-image URLs: https://aioseo.com/docs/aioseo_facebook_tags/ and https://aioseo.com/docs/configuring-the-facebook-settings-for-your-content/. Its `aioseo_twitter_tags` support is **not independently established for installed production** by an offline mocked test.
- The existing 1200px cards use **significant overlaid article-title text**; local dimensions alone do not certify suitability for Discover. In future use genuinely relevant, original, high-quality **low-text image-led editorial art** when available. Do not present stock photos or false after/before outcomes as original evidence. Reference: https://developers.google.com/search/docs/appearance/google-discover .

### Existing social exposure and publication status — do not duplicate
- Connected Metricool brand 7444916 shows Instagram post 2026-10-20 10:01 JST `PUBLISHED` and subsequent Instagram autolist reservations (from Oct 22) `PENDING`. Instagram already has its own scheduler. Asset-generation workflow not posting **does not** mean no active Instagram distribution.
- The owner **already connected Pinterest native RSS** on Oct 16 to the GitHub image-backed feed, targeting the public board; see `docs/pinterest-image-rss-activation-2026-10-16.md`. Whether Pinterest has actually imported a real article Pin from that feed, with correct image and article destination, remains **not verified**. Do not ask to reconnect the feed or enable a second Pinterest Metricool autolist without investigating duplicates.
- The official Threads account (NOT the owner's personal account) recorded daily post views of 317, 295, 41, 892 and 716 for Oct 15–19 respectively in a Metricool read-only query (sum 2,261 **views**, not unique viewers or website sessions). Pinterest outbound fields were 0 or unavailable in that period; that is **not proof that no one visited the website**, nor a complete native-RSS Pinterest Pin audit. The Metricool planner does not list native Pinterest RSS imported pins.
- Reliable breakdown of actual incoming website sessions by Threads/Pinterest/Instagram still requires legitimate GA4 source/medium access. Do not claim GSC search data or Metricool post views are website visits.

### Next safe release gates
1. Establish whether **a native Pinterest RSS Pin actually exists**, has an original Survival40 image and correctly links to the published canonical article. No duplicate creation or feed reset without evidence.
2. Verify one representative article in a **restorable staging WordPress environment**, after inspecting the installed AIOSEO plugin and image URL HTTP delivery. Compare rendered OG tags without changing its canonical URL, layout or banners. Production is not authorized by an offline test.
3. Prepare a controlled, optional **one-for-one** integration of grounded Shiori tips into existing social slots only after proving the pinned live generator and ledger preserve persona, published status and duplicate protections; no extra daily posts.
4. Measure populated native account metrics and GA4 sessions before declaring a distribution channel effective. No Discover placement, ranking, traffic or revenue guarantee.

**Protected:** no WPVibe call, WordPress write, production plugin upload, changed SNS publisher or new paid service in this follow-up.
