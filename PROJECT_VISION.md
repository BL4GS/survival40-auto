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

## Audience, motivation and long-term consequence framing (owner-approved 2026-10-15)
- **Core audience:** men in their 40s, whether single, married, divorced or widowed. The initial image of a single man is one possible reader persona, **not an exclusion criterion**. Do not automatically equate "men's beauty" with dating or sexual appeal.
- **Brand motivation:** Help readers retain agency and self-respect as they age. The owner's personal starting point is **「20代の頃の自分に負けたくない」**: not literally returning to one's 20s, but not surrendering personal style, strength or grooming to age. Inspiration from visual-kei musicians such as HYDE illustrates this *personal* motivation, **not a researched claim that most men feel the same**. Positive attention from others may be welcome, but is not the primary promise.
- **Reader entry point:** Many articles should begin with a concrete question/problem people might search for, including **「じゃあ放っておいたらどうなるのか？」** ("What could happen if I leave this unattended?"). Cover readers who are not already interested in beauty. Search-demand hypotheses must be validated using actual Search Console/keyword evidence; wording alone does not establish demand or rankings.
- **Narrative sequence when appropriate:** (1) name the present-day concern in plain language, (2) show **plausible, evidence-supported longer-term risks** of leaving it unaddressed, e.g. into one's 50s or later, (3) distinguish what is and is not preventable or uncertain, and (4) finish with **small, realistic actions that can start today**. Don't stop at frightening predictions. A product link is optional and only follows demonstrated relevance.
- **Grounded examples, never inevitabilities:** Repeated unprotected UV exposure is a risk factor for photoaging and visible pigmentation; inactivity can contribute to declining strength and later functional limitations; untreated dental caries and periodontal disease can contribute to tooth loss. **Never claim** that skipping sunscreen guarantees a face full of spots at 50, that skipping weight training inevitably causes a bent back or inability to walk, or that lack of oral care guarantees early loss of teeth. Risk varies by circumstances and prevention cannot guarantee an outcome.
- **Editorial restraint:** Do not scare, shame, mock aging or make unsupported personal/medical predictions. No invented "future self" imagery presented as documented outcomes, fabricated before/after proof or claims about the reader's future. Verify the relevant risk/cause using credible evidence, and provide proportionate caveats and professional-care indicators for health topics.
- **Balance:** This is a strong framing option for prevention and explanatory articles, **not a compulsory negative headline or fear hook in every article**. Maintain the established mix of how-to, everyday life, seasonal, Shiori-led and properly matched product/ad-free articles. Keep the answer to the searcher's immediate question accessible early in the piece.
- **Enduring positioning:** **「20代の自分には戻れない。だからといって、40代の自分が劣っている必要はない。」** / **「50代の自分を、今からつくる。」** The opponent in **「40代からの生存戦略、敵は自分」** is giving up on oneself because of age, **not aging people or age itself**. These are editorial compass phrases, not mandatory sentences to paste into every article.
- **Automation requirement:** Apply this audience model and evidence-based future-consequence framework when the AI chooses topics, writes, reviews and refreshes relevant articles; avoid requiring routine owner prompts in each new thread. This document defines the target editorial policy; **it does not assert the current WordPress generator already enforces these new rules**.

## Japanese article-title style (owner preference, 2026-10-15)
- **Avoid the full-width vertical-bar separator 「｜」 in newly generated Japanese article titles and SEO titles by default.** The owner does not naturally write titles as 「前半｜後半」 and finds this mechanical, AI-like and repetitive. A bar is not an SEO requirement.
- Prefer a **natural, complete Japanese headline** that resembles the specific question or concern of the reader; use ordinary particles, commas and question marks when they make the title clearer. Don't force every title to be a question, and don't mechanically repeat one syntactic template.
- Example to **avoid**: 「旦那の加齢臭が気になる｜本人を傷つけずにできる対策と商品選び」. **Preferred voice**: 「旦那の加齢臭が気になるけど、傷つけずに伝えるには？」 or another concise, natural wording appropriate to the actual article.
- Include relevant search terms naturally, without packing several keyword phrases or promises into a two-part heading. Match the article's real content and search intent. Do not mislead by removing necessary qualifying words.
- Apply this voice at topic-planning, draft-title, final post-title and AIOSEO SEO-title stages. A WordPress theme/SEO plugin may have a separate, sitewide brand suffix template; evaluate that separately rather than overriding global formatting just to enforce this preference.
- **Do not bulk-rename existing published posts or change permalinks merely because they contain 「｜」.** Preserve current URLs, SEO signals and internal links; consider specific rewrites only during a justified article refresh with measured evidence and safe URL handling.
- This rule is canonical editorial direction, **not a claim that the installed AI publishing plugin has been modified or is already enforcing it**.

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
