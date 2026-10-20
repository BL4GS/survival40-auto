# GitHub-first WordPress operations — draft preflight (2026-10-20)

## Decision
Use GitHub as the source of truth for automation source and changes. WPVibe is an optional fallback for exceptional authenticated maintenance, **not** a dependency of the normal editorial, publishing, or SEO cycle. Do not spend WPVibe's rolling quota on routine checks or per-post editing.

The canonical objective remains `PROJECT_VISION.md`: autonomous topic discovery, independent research, writing, quality gates, safe publishing, internal linking, and performance feedback. Do not create a parallel article generation engine merely to replace a transport.

## What exists now
- WordPress plugin v0.19.20 has its own article generator; the more complete v0.19.21/v0.19.22 paths are still protected by release/backup gates.
- GitHub weekly `editorial_intelligence` drafts research-only ideas, but the protected WordPress inbox is a staged future plugin feature, **not** a currently confirmed production article-write endpoint.
- `scripts/wordpress/draft_preflight.py` is a **read-only** WordPress REST client. It inspects a single authenticated draft, validates the exact ID, slug and status, and emits a SHA-256 fingerprint of `content.raw` rather than draft HTML or credentials.
- `.github/workflows/wp-draft-readonly-preflight.yml` runs credential-free offline tests for PRs. Its live GET step requires explicit manual dispatch with a confirmation phrase and matching GitHub Actions secrets. Missing secrets or any WordPress redirect are fail-closed.
- The immediate candidate is draft **620**, slug `40s-male-razor-burn-shaving-care`, which had only a partial article body on WordPress on 2026-10-20. A completed proposed HTML article exists separately in the conversation, **not** in GitHub and **not** yet written to WordPress.

## What is deliberately NOT enabled
- No POST/PUT/PATCH/DELETE to WordPress; no article edits, category edits, ads, or publication.
- No production plugin release, `version.txt` bump, activation or restored-DB cutover.
- No assumptions that the GitHub-to-WordPress Application Password is already configured, that a REST route is live, or that an offline test proves server-side behavior.
- A client-side GET and hash comparison alone is **not atomic**: another editor/process could change the post between GET and write. Never claim it provides a safe compare-and-swap.

## Next safe development stages
1. After authorization and site readiness, run the manual **read-only** preflight, verify the exact live draft and category, and keep its fingerprint private in the GitHub Actions artifact.
2. Build an isolated WordPress **draft-only compare-and-swap endpoint** as part of an explicitly versioned future plugin release. Check administrator capability, exact post ID/slug/status, expected raw-content hash, JSON size, single-writer locking and content diff; return conflict instead of overwriting any changed draft. No public posts, promotions, ads, or bulk mutations.
3. Test the endpoint against disposable WordPress including replay, concurrent edits, expired credentials, network failures, Japanese HTML, and rejected attempts to change statuses or unrelated metadata.
4. Only after independent Web+DB recovery rehearsal, ad/publishing state verification and staffed rollout, release the reviewed plugin via the existing guarded release process. Keep previous plugin ZIP, draft inventory, and rollback available.
5. Connect the established GitHub editorial source and WordPress research/quality pipeline, then add performance feedback without requiring routine owner intervention.

## Why this matters
Draft 620 illustrates a transport gap, not a reason to resume WPVibe-based per-post operation. Close the gap once, with guarded infrastructure; use it for future safe draft refreshes only after the controls are proven.
