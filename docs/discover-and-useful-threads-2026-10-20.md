# Survival40 — Discover visibility and useful Shiori posts (2026-10-20)

Status: owner direction accepted in conversation; **implementation is incremental, not a claim of Discover placement or new live posting**. \`PROJECT_VISION.md\` is authoritative if there is any conflict.

## Objective
Stop relying only on users actively searching. Keep search as a durable channel, while strengthening *interest-based discovery* (Google Discover and Pinterest) and useful native Threads publishing under 栞さん's existing identity. The owner's personal X/Threads profiles remain personal and unmodified. Do not create new daily work.

## A. Google Discover: operational facts and guardrails

Official Google documentation:
- https://developers.google.com/search/docs/appearance/google-discover?hl=ja
- https://developers.google.com/search/docs/appearance/google-images?hl=ja

1. Content indexed by Google and compliant with Discover policies is **automatically eligible**, without application, special Discover markup, or guaranteed placement.
2. Article titles should be informative and natural, not sensational or misleading.
3. Google recommends relevant high-quality images at least 1200 px wide and over 300,000 total pixels, with sufficient landscape cropping room; use \`max-image-preview:large\` or AMP. Use a representative \`og:image\` or schema image to help Google select the preferred image. Avoid generic logos and overly text-heavy cover art.
4. Published articles may be selected even when older; do not stamp fake freshness, invent testimonials, write dubious medical promises, or change canonical URLs for Discover.
5. Search Console's Discover performance section may appear only after sufficient impressions. A missing report **does not prove ineligibility**.

### Existing implementation and current gap
- Original brand social assets can be generated in GitHub, but image files by themselves **do not add WordPress \`og:image\` metadata**.
- The existing \`scripts/social/check_og.py\` daily 10:25 JST workflow is read-only and inspects the public HTML of up to ten items already in the verified Pinterest RSS.
- This PR extends its same fetched HTML head to report HTML robot preview hints, \`og:image\` count and declared dimensions as **observations**, not claims about the image's actual bytes or Discover eligibility.
- HTML \`meta\` cannot detect the HTTP \`X-Robots-Tag\`, schema images, search index state, or live Google Discover impressions. The report explicitly labels these unverified.
- Any future change to AIOSEO's metadata, WordPress media/featured images or \`max-image-preview\` must first be isolated, independently backed up and regression-tested. Only the existing SEO component should emit these tags; **never inject competing duplicate metadata**.
- Do not replace site layout, Shiori visual identity, or live affiliate banners in the article to solve the card-preview problem.

### Future release checkpoint (separate PR)
A staging-only proof on one safe article should verify original image provenance, proper public image URL, 1200px+ true dimensions, matching title/body, existing AIOSEO output, canonical URL, front-end view and precise rollback. Don't switch all posts without evidence. Monitor Search Console Discover data when available. **No automated promise of placement.**

## B. 栞さん Threads: use more of the existing reach without turning her into an advice bot

The existing scheduled workflow publishes to verified \`@survival40_jp\` in its four daily slots and a separate, source-checked nightly article mention. **The 4-slot workflow checks out immutable SHA \`030e1f8a4cb23550802653b1dbcc97a263473566\`**, so a change to main's \`threads/editorial.json\` or \`scripts/threads/compose.py\` alone has **zero proven effect on live copy**. Never silently swap pinned refs or issue live Meta posts to test tone.

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
