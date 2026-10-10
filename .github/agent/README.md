# Survival40 Nightly AI Engineer — guarded pilot

## Current state (2026-10-11)
- GitHub Actions schedule: daily 18:20 UTC (= 03:20 JST), or manual workflow_dispatch.
- One bounded Gemini 3.5 Flash-Lite API request per run, using the repository secret GEMINI_API_KEY (GOOGLE_API_KEY also accepted). No fallback to a paid model and no automatic quota retry.
- Model produces one proposal and one Python unittest under `.github/agent/generated_tests/test_s40_*.py`. No other AI-modified paths are permitted.
- A separate **secret-free** validation job checks the trusted validator, constrains imports and file writes, and executes a fixed unittest command. Model-suggested shell commands are NEVER executed.
- Only a passing candidate may be committed to `ai/nightly-candidate` and offered as a **draft PR**, never merged or deployed automatically.
- The branch acts as a hard stop: if `ai/nightly-candidate` exists, the next nightly run does not call Gemini or create a second proposal. Owner must review/merge/close and remove the branch before the next candidate.
- Live WordPress, existing posts, A8 approval state, release workflow, and release asset are untouched by nightly AI.
- `PROJECT_VISION.md` remains the binding editorial direction.

## Permission prerequisite
First pilot: validation succeeded, and the AI-authored test was committed to `ai/nightly-candidate`.
GitHub Actions was denied permission to open a PR:
`GitHub Actions is not permitted to create or approve pull requests`.
A draft PR was then opened through the connected GitHub integration: https://github.com/BL4GS/survival40-auto/pull/1

For future fully automatic draft PR creation, the owner must explicitly enable **Settings → Actions → General → Workflow permissions → Allow GitHub Actions to create and approve pull requests** (when supported by repository policy). This is not equivalent to authorizing auto-merge; merging remains manual. Until enabled, Actions can still produce and validate a candidate branch but cannot make the PR itself.

## Known limitations
- This is **not** yet an unrestricted self-modifying engineering agent. It can add one safe test per nightly cycle, not rewrite PHP, secrets, plugins, release workflow or production content.
- The static AST guard is defense in depth, not a proof of all Python behavior. Generated tests always run in a separate job without Gemini credentials and with read-only GitHub privileges.
- Gemini free tier may return 429 or 404 or other errors; a run then fails safely. The project's actual billing tier is controlled in Google AI Studio and must remain Free if paid usage is unacceptable.
- CI SUCCESS is not the same as production validation, backups or a successful update on the live WordPress site.
- Review the test for meaningful assertions before merging; trivially passing tests provide little protection.

## Safe expansion plan
1. Owner reviews draft PR #1 and repository workflow permissions.
2. Implement auto-select of an existing tracked issue or backlog test gap (without broadening the allowlist).
3. Add isolated packaging/regression checks for release candidate consistency.
4. Only after consistent review results, consider **draft-PR-only** changes to allowlisted non-release staging scripts, with tests and human merge.
5. Production release still requires backup, rollback and manual approval gates in docs/release-01921-production-safety.md.
