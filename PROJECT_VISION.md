# Survival40 — Project Vision (Canonical)

Status: Accepted by owner on 2026-10-11. This document defines the project objective, not a claim that all functions have been implemented.

## North star
Survival40 is an autonomous, reader-first WordPress information medium. AI independently discovers topics, researches and verifies information, writes and improves articles, selects and legally acquires relevant affiliate offers/products, publishes suitable articles, maintains links/content, and grows the library. The owner's routine role should be limited to optional SNS promotion and rare strategic decisions / exceptions. Do not introduce per-article manual work as the normal operating model.

## Editorial principles
- **Reader value comes before advertisements.** Do not require affiliate links or products in every article; an article may contain **zero advertisements**.
- Content is a deliberate mix of helpful how-to/explainer articles, seasonal and timely topics, and carefully matched product/affiliate content.
- **Guide Shiori (栞さん)** serves as a recurring site guide/narrative presenter for appropriate explanatory, practical and seasonal articles. Keep her established persona and visual assets consistent, and preserve existing presentation behavior. Do not turn every appearance into a promotion.
- Example no-ad topic: advice about easing eye fatigue, including gentle practical self-care or massage guidance. Health content must not make unsupported therapeutic claims; mention appropriate cautions and when professional care is warranted.
- Other examples: seasonal everyday concerns and life events, with useful advice as the core.
- Advertising is conditional: match an ad only when its actual offer helps the specific article's reader, eligibility and links are verified, disclosures are clear, and platform/program policies are satisfied. If no good match exists, publish without an ad.
- Amazon: automate through authorized available methods, never fabricate product facts, prices, availability, or affiliate links. A8/other networks: respect actual access, approval, usage rules and verification requirements. If automated retrieval is unavailable, do not imply it works.
- Prioritize factual accuracy, editorial quality, relevance, user trust and safe handling of health/financial topics over sheer article count.

## Autonomous workflow (target)
1. Discover demand: queries, seasonality, existing gaps and trend relevance.
2. Select a genuinely useful topic; choose editorial type and determine whether commercial intent exists.
3. Research reliable sources, verify key claims and originality; avoid duplicative or thin posts.
4. Write and format the article; add Shiori guidance where suitable.
5. Independently assess affiliate suitability and retrieve verified eligible offers/products only if appropriate.
6. Apply factual, quality, compliance, SEO, duplication and safety gates. Rework or defer if failing.
7. Publish automatically when all gates pass, including **ad-free** articles.
8. Re-evaluate aging articles, dead links, content accuracy and offers; update or remove as appropriate.
9. Monitor failures, stop unsafe actions, log reasons and allow recoverability, without routine manual intervention.

## Architecture and release rules
- WordPress and existing posts, frontend design, Shiori/navigator assets and established features must be protected.
- Plugin upgrades should occur safely and automatically, with verified version metadata, rollback/backup and activation continuity. Never confuse test success with real-site verification.
- Never switch affiliate banners on by default merely to raise monetization.
- Do not silently activate unreviewed campaigns, break platform terms, overwrite published content or change owner-facing brand decisions.
- Test in isolation before production; build distributable ZIP from the same code/assets and record checksums.
- Separate **vision** from **implemented capability**, and document unresolved external integrations.

## Decision priority
1. Reader trust and safety.
2. Editorial utility and factual accuracy.
3. Fully autonomous, low-maintenance operation.
4. Discoverability and sustainable affiliate monetization.
5. Volume / speed.

## Owner's ongoing role
Optional SNS promotion, major policy decisions and exceptional intervention; not article-by-article writing, ad selection, routine uploads or plugin ZIP installations.

## Change control
Do not redefine the north star due to a chat/thread change. Changes to this vision require explicit owner agreement. New sessions should read this document before deciding development priorities. Specific implementation plans and current release versions live elsewhere and may change independently.
