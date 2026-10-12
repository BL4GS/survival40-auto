# Survival40 Editorial Topic Intelligence

Status: review branch; independent planning-support component, **not** the WordPress plugin's existing planner.

## Purpose
Identify what the site has **not yet covered** by analyzing its existing published article titles and excerpts. The proposal shortlist helps autonomous editorial strategy without imposing routine topic selection on the owner.

## Operating boundary
- Public WordPress REST data only, reusing `site_audit.audit.fetch_posts`. No WordPress authentication and no edits.
- One bounded Gemini Flash-Lite JSON request per weekly run, no retries, no paid fallback. Secrets stay in Actions Secrets, not reports.
- Up to five validated article ideas across skincare, fitness/body and daily living.
- Look for concrete reader needs; suppress repeated published titles and repeated candidates.
- **Default: no advertising.** An optional product mention is only an editorial possibility, never a verified affiliate entitlement or command to insert ads.
- Health/scientific claims, product facts, sources, holiday claims, search volume and trend demand have **not** been verified at this stage. Research questions are explicit, sources are not invented.
- Shiori is a site navigator and does not claim real product usage or experience.
- Candidate output is advisory `concept_only_not_researched`. This is a feeder for a future separately reviewed plugin planning handoff; it does **not** generate or publish an article, touch affiliate settings, rewrite WP data or send Threads posts.

## Workflow and reporting
- `.github/workflows/editorial-topics.yml` validates the planner for pull requests without Gemini credentials.
- Once merged, scheduled **Monday 05:10 JST** (GitHub time may drift); manual dispatch supported.
- Data inputs: up to 90 public published titles and brief excerpts, not unpublished material.
- Output in GitHub Actions artifacts: `editorial-output/topics.md` and `topics.json`, retained 21 days.
- Fail closed on lack of published titles, Gemini quota errors, malformed JSON, duplicate titles and unsupported candidate structure.
- A successful workflow does not imply the topics have proven reader demand. There is no external keyword-volume or trend feed.
- Before integrating directly into the WordPress auto-publisher, map this schema to the existing `auto_category_map()` and article research/publishing gates. Do not create a second independent WordPress publishing pipeline.

## Scope of duplicate detection
Normalization + character-sequence similarity identifies clear paraphrases of existing titles but **cannot rule out a semantic duplicate**. The existing WP planner and article research stage must independently check intent and substance.

## Future target
`Public article inventory → gap candidates → source discovery and direct claim support → quality checks → existing WordPress automatic planner/publisher`.

Production rollout remains blocked until the project release safety requirements in `docs/release-01921-production-safety.md` are met.
