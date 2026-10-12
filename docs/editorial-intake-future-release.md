# Future WordPress editorial intake — staging only

The weekly GitHub planner produces unresearched article briefs in the survival40.wp_plan_handoff.v1 schema. The present WordPress plugin cannot accept these directly. This staging-only patch adds a protected queue; it does not create or publish articles.

## Safeguards
- Code: .github/scripts/patch_editorial_intake_next.py; NOT used by current 0.19.21 release.
- Future endpoint: GET/POST /wp-json/survival40/v1/editorial-plans (or equivalent rest_route URL). Only current_user_can('manage_options') can read/post, including WordPress Application Password authentication.
- Max 50KB payload and five plans; exact schema, research-needed markers and eight WordPress category names required.
- No content or status writes: stores max 30 research-only briefs in s40_editorial_plan_queue_v1; no post creation, API generation, or ad activation.
- Rejects duplicate deliveries, already-existing WordPress titles across publish/draft/pending/future/private, and invalid/misleading research validation claims.
- A conservative single-writer lock guards option writes. An unexpected fatal can leave a stale lock; investigate instead of blindly clearing and replaying an uncertain delivery.

## Staging verification
- .github/workflows/editorial-intake-staging.yml reconstructs current 0.19.21 code only in CI, applies this future-version patch and staged fail-closed planner patch, checks PHP syntax, and runs PHP WordPress-stub behavior tests.
- This is not a substitute for isolated real-WordPress activation and integration testing before production.

## Before remote delivery is enabled
1. Verify offsite hosting/WordPress database + wp-content backup and rollback path.
2. Release a separately versioned plugin, confirm actual live plugin activation and REST route.
3. Create a WordPress Application Password for an explicitly authorized account; store only in GitHub Actions Secrets.
4. Add a narrowly gated GitHub transport with strict endpoint and account checks; never publish WordPress posts directly from GitHub.
5. Confirm WAF compatibility without disabling global site protection and reconcile failed deliveries safely.
6. Independently verify sources, reviewer score, all existing post statuses and ad policy before any future queue consumer creates an article.

This implementation is a safe receiving endpoint, not an enabled autonomous article publishing feature.
## Staged queue research consumer (future version only)
- Next patch: .github/scripts/patch_editorial_consumer_next.py, applied after the intake and fail-closed planner patches, never by current 0.19.21 release.
- When the existing WordPress auto-cycle is enabled, claim at most one plan with awaiting_independent_research. Recheck current WordPress public and private titles before generating.
- Map the plan into the existing `generate_planned_article` pipeline: the normal Gemini source discovery, claim review, rewrite and deterministic quality checks remain in force. Queue plans must have no affiliate candidate and cannot turn on A8/Amazon output.
- If independently matched sources, review score or safety scan fail, **do not even create a draft** for that queued idea; mark held_after_research_failure. A processing plan is not blindly retried after an uncertain interruption.
- On passing all gates, create **draft only** and record post_id, regardless of the site's global `auto_publish_general` flag. Additional, separately reviewed safeguards are required before queue proposals may be auto-published.
- Normal existing planner remains available when the intake queue is empty. This staged consumer makes no production changes until a later controlled plugin release.
- Static/php-stub tests and isolated reconstructed PHP syntax checks have passed; a real isolated WordPress integration and ConoHa backup restore test are still required.