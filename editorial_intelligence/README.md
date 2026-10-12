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

## WordPress planner handoff — additional safe artifact

The weekly workflow now runs \`python3 -m editorial_intelligence.bridge\` after producing \`topics.json\`.

- The live v0.19.21 release-review package uses **eight Japanese category names**, not the three broad suggestion buckets \`skin/body/daily\`: \`肌・老け見え\`, \`髪・頭皮\`, \`ニオイ・清潔感\`, \`口・歯\`, \`疲労・睡眠\`, \`体型・筋力\`, \`食事・栄養\`, \`40代の不調\`.
- A deterministic subject router maps concrete topics to one of those names. Unrecognized, multi-topic, unsafe medication/treatment and contradictory buckets are **held** rather than guessed.
- Refreshes the public article title inventory before generating the handoff, to catch topics published after the original AI suggestion.
- \`editorial-output/wp-plan-handoff.json\` contains a structured \`plugin_planner_input\` for future research, including \`title, keyword, category, excerpt, seo_title, amazon_query, reason\`, plus independent \`editorial\` and \`safety\` fields.
- Every plan is \`needs_independent_source_research\`, with \`publish_authorized=false\`, \`no_affiliate_assigned=true\`, \`ready_to_publish=false\`. \`amazon_query\` is always empty. It is not an API request and is **never imported automatically into the site** at this stage.
- Broad \`requires_health_evidence_review\` is preserved even when the matched WP category is technically non-YMYL.
- Exact WordPress drafts/private/future posts cannot be read via the public REST endpoint. The eventual authenticated plugin consumer **must** recheck those too and enforce its own safety and quality gates.
- The weekly output is an intermediate *planning artifact*. It cannot itself create drafts/posts or bypass WordPress research, medical claim review, source verification or release approval.

The generated \`keyword\` is a wording candidate only; this stage has not measured search volume.
